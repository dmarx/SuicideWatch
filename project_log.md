# The idea

blah blah blah

# Getting the data

## EC2

In the past I’ve run scraping jobs like this from my laptop, but it’s not a good system. If I want to take my laptop somewhere or restart, the job is interrupted. Additionally, running the laptop all the time like that can generate some heat, and keeping your computer hot for a long time reduces its lifespan. To preserve my hardware and make it easier to let the scrape go on uninterrupted, I spun up an EC2 host to run the scraper. The scraper writes to a sqlite database, which is on the same host. I’m interested in serverless architectures and am pretty sure there’s a way I could glue together lambda with other AWS products to accomplish this without spinning up a host, but the host was cheap and I didn’t want to unnecessarily delay getting to the NLP component of the project. I had also considered using one of AWS dedicated database instances to host the data, but I’m pretty sure that would’ve been way overkill and expensive.

When setting up EC2, I selected a t2.micro instance because I knew this component wouldn’t be computationally intensive. When configuring this instance, I didn’t modify the inbound security rules, meaning only port 22 was open for SSH (TCP). In retrospect, I should have opened up HTTP/HTTPS as well to allow me to set up web-accessible jupyter notebook server. Without this, I could only run code by SSH-ing into the box, which wasn’t a nuisance or anything, but it a notebook server would’ve been convenient.

I'm using github as an intermediary to transfer project code to the host. In addition to being a bit more convenient than SCP-ing (imho), it's a simple way to enforce version controling my work. It also encourages me to test my code locally before committing, since I don't want to transfer bugs into my production environment. Another thing I like about github is the issue tracker, which is a great place to log my project backlog so I can easily pick up the project if I need to put it on the back burner for a while.

## Downloading data

### PSAW

Reddit doesn’t make historical data particularly easy to access, but the pushshift.io project does. I decided to pull my data from pushshift and built a simple API wrapper to facilitate accessing this data. I shared that project on reddit, and it has since gained a small following.

### DbApi

From here, I build up the backend architecture piecewise, starting with a module to serve as a database interface. This has become a standard practice for me in basically any project. I find that this approach reduces repeated code, adds some nice organization to the project by keeping most of the database stuff in one place, and ensures that I access the same database the same way everywhere in the project.

The module supports the “DbApi” class. The __init__ function takes a path to a database as input and checks to see if necessary tables exist. If they don’t, it runs an external script that defines the schema. I find it’s convenient to define the schema in one place like this: it essentially becomes a kind of documentation. I refer to my schema.sql file all the time as a quick reference in case I forget the names of tables or columns.

### /r/SuicideWatch sentences

To start with, the database just contained one table: “submissions”. This was sufficient for the first phase of the project, which was just downloading submission title and selftext for all /r/SuicideWatch submissions. I wanted to break these up into component sentences, so I added a “sentences” table to store these sentences.

At this point, the project had two main functions it needed to support: downloading historical submissions from that one subreddit, and parsing out unique sentences from those submissions. I’m data greedy and decided it would be cool if I could keep updating this dataset moving forward, so I had to build out additional functionality to support updating with new content rather than just “backfilling” historical content. To make it easier to initiate these processes from cron, I added a script to handle a CLI that can kick off different functionality. At this point, the CLI had three arguments, each corresponding to a different function to run: --backfill-submissions, --get-new-submissions, and --parse-sentences.

After downloading some data, I started playing with it to get a feel for what I had. One of the first things I tried was querying for the most common sentences. I was surprised to see that several of these were only one sentence long, and realized this was an artifact of people. writing. like. this. Additionally, there were other short sentences that were common in the data that were definitely not indicative of my target specifically, like “Fuck it.” I decided that it would be helpful to constrain attention to sentences with at least three characters (which I determined by checking that there were at least two spaces).

Ignoring short sentences had the consequence that some submissions wouldn’t have any sentences stored in the sentences table. This was an issue because the sentence parsing step involved querying for any records that didn’t have corresponding sentences. As I collected more data, this step took longer and longer: I was accumulating sentences that would get unnecessarily reviewed during each sentence parsing phase. To mitigate this, I added a flag to indicate if a submission had been processed and could be ignored in sentence parsing.

### Random sentences

The /r/SuicideWatch submissions gave me content for the positive class, but I still needed negative class data to train my classifier. I decided to download random reddit comments in batches, parse sentences from each batch, and repeat the process until I had about as many random sentences as positive class sentences. I added a comments table, and several CLI arguments (--subreddit, --comments, --n, --batch-size…).

This phase proved surprisingly problematic. Many of the /r/SuicideWatch submissions were long self posts, giving me about 15 sentences per submission on average. Random comments on the other hand only gave me two sentences per comment on average. This meant the comments table grew to be much larger than the submissions table, and once again I experienced performance issues in the sentence parsing phase. I mitigated this issue by eliminating the query entirely: I added staging tables that the scraper would write content to, then the sentence parser could just grab all the records from these much smaller tables and transfer their contents to the main tables after sentences had been parsed.

Another issue was counting sentences for parity between the positive and negative classes. This query could still benefit from some optimization, but I got significant improvement by adding indices. I’ve got all the data I need for now, but if I feel the need I can improve this query by constructing a statistics table that would maintain a running count of sentences in each class, rather than recalculating that number on the fly each time I need it with an expensive query.

### Handling bots

After downloading random content I checked for the most popular sentences in that data. The results were clearly dominated by /u/Automoderator. I realized I hadn't accounted for bots at all and they would taint my data if I didn't. I deleted all comments made by /u/Automoderator and any user with "bot" in their username, and added filters in the scraping code to ignore comments authored by these users. Additionally, I checked to see who the most prolific authors were and discovered many more bots (several masquerading as regular users). I haven't accounted for these yet, but will probably handle them by ignoring content from users who have more than X comments in my data. /u/Stuck_in_the_matrix has a bot dataset as well he constructed by looking at the time between subsequent comments by the same user, so I may use that report as part of my filtering methodology as well.

## Additional data sources

My plan for constructing the classifier is going to result in me tagging a lot of sentences as positive class that were authored by suicidal people, but aren't actually expressing any concerning ideations. One way I might try to buffer this is to include content from somewhere like /r/depression that hopefully would be mostly "blue" state-of-mind, but not suicidal.

I took a look in /r/depression, and there's definitely plenty of suicidality. I decided to poke around and see what else there was using pushshift's subreddit recommender, querying for suicidality. https://pushshift.io/reddit/subreddit-explorer/

Lordy.

There are a ton of depression/suicide/psychosis oriented subs. There are a few that are actually trying to help people perform the act. The main one was banned, but there are still some skirting the rules.

Another thing I tried was grabbing a random redditor expressing suicide and enumerate their top subreddits, and the top subreddits of users active in /r/depression. Might not be a bad idea to start characterizing the reddit mental health community/network. Could target interventions at these subreddits. Might be redundant, considering the high occurrence of suicidal ideation in those subs. My tool would probably be more useful in getting help to someone who isn't addressing a community where people expect to find suicidal ideations.



# Next steps

## Data

* Handle rest of the bots, download more random content if necessary
* Add a 'label' code/tag/table to concretely identify content wrt to the classification test
* Download /r/Depression submissions to represent "gray area" data
* Construct a train/test split
* Download /r/depression data to represent gray area. Might be a good test set, or a way to filter dark-but-not-dangerous content from the positive class. From eyeballing the sub, may actually be a fair amount of suicidality expressed their, so more likely to be useful as a qualitative test set
* Explore incorporating content from other mood-focused subreddits to help model the author's frame of mind. /r/WholesomeMemes, /r/MadeMeSmile...
* Query user histories to try to identify users who may have actually followed through. Can we build a classifier to detect a difference between a "cry for help" and someone who really is about to make a bad decision?

## Modeling

* Set up sagemaker for training
* Build a naive bayes classifier to serve as a baseline
* Use pseudolabeling to try to filter false positives from the positive class dataset
* Build a classifier using pretrained wordvectors
* Train my own reddit-specific word vectors
* Train a bespoke character-level RNN language model
* Train a classifier on raw character inputs without an isolated language model component

## Misc

* Start thinking more about how to operationalize this. Public API is easy, but are there active interventions that might be worth exploring? A bot that PM's people who might be having a bad time? Maybe partner with a suicide hotline as a proactive monitoring service to reach out to people in danger instead of waiting for them to call?

# Other relevant subreddits

## Depression/suicide locus
* /r/Suicide_help
* /r/suicidology
* /r/SuicideNotes
* /r/SanctionedSuicide - banned
* /r/suicidology
* /r/suicide
* /r/depression
* /r/raisedbynarcissists
* /r/FreeToGo
* /r/TimeToGo
* /r/depression_help
* /r/CPTSD
* /r/WeListenToYou
* /r/trolldepression
* /r/BPD_friends
* /r/BreakUp
* /r/DepressionAndPTSD
* /r/AvPD
* /r/2meirl42meirl4meirl - Maybe comments. Users, at least.
* /r/death
* /r/mentalhealth

## depression/suicide support
* /r/SuicideWatch
* /r/reasonstolive
* /r/depression_help
* /r/WeListenToYou
* /r/SuicideBereavement

## Depression/suicide anti-support
* /r/SanctionedSuicide - banned
* /r/Suicidology - prob should be banned, needs heavy moderation if it's actually academic
* /r/FreeToGo

## Depression/suicide academia
* /r/suicidology

## Predominantly positive mindset content
* /r/reasonstolive
* /r/WholesomeMemes
* /r/MadeMeSmile

## Misc High risk communities
* /r/TalesFromTheMilitary
* /r/TransCommunity
* /r/needadvice
* /r/advice
* /r/fosterit
* /r/homeless

## Suicide/depression resources
From /r/WeListenToYou sidebar:
* Suicide hotlines: https://www.reddit.com/r/SuicideWatch/wiki/hotlines
* Domestic violence shelters: https://www.domesticshelters.org/search#?page=1
* /r/personalfinance, apparently
* Warmlines:
  * Anne Arundel County Crisis Warmline (MD): 410-768-5522
  * The Cincinnati Warmline (OH): (513) 931-9276

## Useful pushshift shorthands (maybe add some PSAW functionality)
* Subreddit (top) authors: http://api.pushshift.io/reddit/comment/search/?subreddit=depression&aggs=author&limit=0
* User top subreddits: http://api.pushshift.io/reddit/comment/search/?author=AloneOrAbused&aggs=subreddit&limit=0
