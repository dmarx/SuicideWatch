# 1. The idea

blah blah blah

# 2. Getting the data

## 2a. EC2

In the past I’ve run scraping jobs like this from my laptop, but it’s not a good system. If I want to take my laptop somewhere or restart, the job is interrupted. Additionally, running the laptop all the time like that can generate some heat, and keeping your computer hot for a long time reduces its lifespan. To preserve my hardware and make it easier to let the scrape go on uninterrupted, I spun up an EC2 host to run the scraper. The scraper writes to a sqlite database, which is on the same host. I’m interested in serverless architectures and am pretty sure there’s a way I could glue together lambda with other AWS products to accomplish this without spinning up a host, but the host was cheap and I didn’t want to unnecessarily delay getting to the NLP component of the project. I had also considered using one of AWS dedicated database instances to host the data, but I’m pretty sure that would’ve been way overkill and expensive.

When setting up EC2, I selected a t2.micro instance because I knew this component wouldn’t be computationally intensive. When configuring this instance, I didn’t modify the inbound security rules, meaning only port 22 was open for SSH (TCP). In retrospect, I should have opened up HTTP/HTTPS as well to allow me to set up web-accessible jupyter notebook server. Without this, I could only run code by SSH-ing into the box, which wasn’t a nuisance or anything, but it a notebook server would’ve been convenient.

## 2b. Downloading data

Reddit doesn’t make historical data particularly easy to access, but the pushshift.io project does. I decided to pull my data from pushshift and built a simple API wrapper to facilitate accessing this data. I shared that project on reddit, and it has since gained a small following.

From here, I build up the backend architecture piecewise, starting with a module to serve as a database interface. This has become a standard practice for me in basically any project. I find that this approach reduces repeated code, adds some nice organization to the project by keeping most of the database stuff in one place, and ensures that I access the same database the same way everywhere in the project.

The module supports the “DbApi” class. The __init__ function takes a path to a database as input and checks to see if necessary tables exist. If they don’t, it runs an external script that defines the schema. I find it’s convenient to define the schema in one place like this: it essentially becomes a kind of documentation. I refer to my schema.sql file all the time as a quick reference in case I forget the names of tables or columns.

To start with, the database just contained one table: “submissions”. This was sufficient for the first phase of the project, which was just downloading submission title and selftext for all /r/SuicideWatch submissions. I wanted to break these up into component sentences, so I added a “sentences” table to store these sentences.

At this point, the project had two main functions it needed to support: downloading historical submissions from that one subreddit, and parsing out unique sentences from those submissions. I’m data greedy and decided it would be cool if I could keep updating this dataset moving forward, so I had to build out additional functionality to support updating with new content rather than just “backfilling” historical content. To make it easier to initiate these processes from cron, I added a script to handle a CLI that can kick off different functionality. At this point, the CLI had three arguments, each corresponding to a different function to run: --backfill-submissions, --get-new-submissions, and --parse-sentences.

After downloading some data, I started playing with it to get a feel for what I had. One of the first things I tried was querying for the most common sentences. I was surprised to see that several of these were only one sentence long, and realized this was an artifact of people. writing. like. this. Additionally, there were other short sentences that were common in the data that were definitely not indicative of my target specifically, like “Fuck it.” I decided that it would be helpful to constrain attention to sentences with at least three characters (which I determined by checking that there were at least two spaces).

Ignoring short sentences had the consequence that some submissions wouldn’t have any sentences stored in the sentences table. This was an issue because the sentence parsing step involved querying for any records that didn’t have corresponding sentences. As I collected more data, this step took longer and longer: I was accumulating sentences that would get unnecessarily reviewed during each sentence parsing phase. To mitigate this, I added a flag to indicate if a submission had been processed and could be ignored in sentence parsing.

The /r/SuicideWatch submissions gave me content for the positive class, but I still needed negative class data to train my classifier. I decided to download random reddit comments in batches, parse sentences from each batch, and repeat the process until I had about as many random sentences as positive class sentences. I added a comments table, and several CLI arguments (--subreddit, --comments, --n, --batch-size…).

This phase proved surprisingly problematic. Many of the /r/SuicideWatch submissions were long self posts, giving me about 15 sentences per submission on average. Random comments on the other hand only gave me two sentences per comment on average. This meant the comments table grew to be much larger than the submissions table, and once again I experienced performance issues in the sentence parsing phase. I mitigated this issue by eliminating the query entirely: I added staging tables that the scraper would write content to, then the sentence parser could just grab all the records from these much smaller tables and transfer their contents to the main tables after sentences had been parsed.

Another issue was counting sentences for parity between the positive and negative classes. This query could still benefit from some optimization, but I got significant improvement by adding indices. I’ve got all the data I need for now, but if I feel the need I can improve this query by constructing a statistics table that would maintain a running count of sentences in each class, rather than recalculating that number on the fly each time I need it with an expensive query.
