const { connectToMongo } = require("./mongoClient");
const { ObjectId } = require("mongodb");
const { getArticles } = require("./getArticles");
const { getFacts } = require("./getFacts");
const { getSources } = require("./getSources");
const { getTopics } = require("./getTopics");

const processTopics = async () => {
    let attempts = 0;
    const maxAttempts = 2;
    const dbName = "NewsDive";//"NewsDive"; 
    const mongoClient = await connectToMongo();
    const db = mongoClient.db(dbName);
    const topicsToProcess = [];

    while (attempts < maxAttempts) {
        try {
            console.log("Cron: Getting topics");
            const topics = await getTopics(db);
            console.log("topics debug", topics[0]);
            console.log("Cron: Getting articles for each topic");
            for (let topic of topics) {
                const topicId = new ObjectId(topic._id);
                // if (topic.isArticlesProcessed) {
                //     topicsToProcess.
                //     continue; // skip if already processed
                // } 
                
                console.log(`Cron: Getting articles for ${topic.topic} of id ${topic._id}`);
                const articlesDoc = await getArticles(db, topic);
                topicsToProcess.push({ topic, articlesDoc });

                // Update the topic property to show it's being processed
                const topicsCollection = db.collection("topics");
                await topicsCollection.updateOne({ _id: topicId }, {
                    $set: { isArticlesProcessed: true },
                });
            }
            console.log("Cron: Finished processing topics");
            processFactsandSources(db, topicsToProcess);
            break;
        }
        catch (error) {
            attempts++;
            console.log(`Attempt ${attempts} failed: ${error}`);
            if (attempts === maxAttempts) {
                console.log("Max attempts reached. Exiting.");
                break;
            }
        }
    }
};

const processFactsandSources = async (db, topicsToProcess) => {
    console.log('Entered processFactsandSources function');
    // let attempts = 0;
    // const maxAttempts = 2;
    try {
      await Promise.all(
        topicsToProcess.map(async ({ topic, articlesDoc }) => {
          try {
            console.log(`Cron: Getting facts for ${topic.topic} of id ${topic._id}`);
            await getFacts(db, topic, articlesDoc.articles);
  
            console.log(`Cron: Getting sources for ${topic.topic} of id ${topic._id}`);
            await getSources(db, articlesDoc);
  
            console.log(`Cron: Finished processing for ${topic.topic} of id ${topic._id}`);
          } catch (error) {
            console.error(`Error while processing topic ${topic.topic}: ${error}`);
          }
        })
      );
    } catch (error) {
      console.error(`Error while processing facts and sources: ${error}`);
    }
  };

// async function processFactsandSources(db, topicsToProcess) {
//     console.log('Entered processFactsandSources function');
//     const allPromises = topicsToProcess.map(async ({ topic, articlesDoc }) => {
//         try {
//             console.log(`Cron: Starting parallel tasks for ${topic.topic} of id ${topic._id}`);
            
//             // Parallelize the getFacts and getSources functions for a single topic
//             await Promise.all([
//                 getFacts(db, topic, articlesDoc.articles),
//                 getSources(db, articlesDoc)
//             ]);

//             console.log(`Cron: Finished parallel tasks for ${topic.topic} of id ${topic._id}`);
//         } catch (error) {
//             console.error(`Error while processing topic ${topic.topic}: ${error}`);
//         }
//     });

//     // Wait for all topics to be processed
//     await Promise.all(allPromises);
// };



module.exports = { processTopics };
