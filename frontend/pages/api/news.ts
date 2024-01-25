import clientPromise from "@/lib/mongodb";
import { WithId, Document } from "mongodb";
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

export default async (req: NextApiRequest, res: NextApiResponse) => {
    //set api header
    const headers = {
        "Ocp-Apim-Subscription-Key": process.env.BING_NEWS_API_KEY || "",
    };

    try {
        console.log("Checking if topics exist in database");
        // Checking if topics exist in mongodb database
        // if topics exist, return topics
        // if topics do not exist, get topics from bing news api
        const client = await clientPromise;
        const db = client.db("NewsDive"); //client.db("NewsDive");
        const collection = db.collection("topics");
        const host = "http://" + req.headers.host;
        const isDebug = true; //-- true 
        // get topics for today
        const today = new Date();
        console.log("Current host name: " + host);
        const date =
            today.getFullYear() +
            "-" +
            (today.getMonth() + 1) +
            "-" +
            today.getDate();
        console.log("Date: " + date);
        // const date = "2023-10-15"; // frozen date for debugging
        
        const query = { date: date };
        const topics = await collection.find(query).toArray();
        if (isDebug){
            topics.splice(8);
        }
       
        console.log("Topics in database: " + topics.length);
        console.log("Topics", topics)       
        
        const trackedTopicsQuery = {
            $or: [{ isTrackedTopic: true }, { isPinnedTopic: true }],
        };
        let trackedTopics = await collection.find(trackedTopicsQuery).toArray();

        if (topics.length > 0) {
            //print current host name

            console.log("Topics exist in database");
            res.setHeader("Content-Type", "application/json");
            //cache for one day
            res.setHeader("Cache-Control", "public, max-age=0");
            trackedTopics = trackedTopics.filter(
                (t) => topics.findIndex((t2) => t2._id.equals(t._id)) === -1
            );
            let topicsToReturn = topics.concat(trackedTopics);
            console.log("Topics to return: " + topicsToReturn.length); 

            res.end(JSON.stringify(topicsToReturn));
            return;
        } else {
            console.log("Topics do not exist in database frontend call");
            //call createNewsTopics api
            //save topics to mongodb database

            const topics = await fetch(host + "/api/createNewsTopics");
            const topicsData: any = await topics.json();
            const topicsDataArray = topicsData
                .replace(/[\[\]"]+/g, "")
                .split(",")
                .map((topic: string) => topic.trim());
            console.log("Saving topics to database");
            const topicsToSave = topicsDataArray.map((topic: string) => ({
                topic: topic,
                date: date,
                createdAt: new Date(),
                isArticlesProcessed: false,
                isTrackedTopic: false,
                isPinnedTopic: false,
            }));
            // if (isDebug) {
            //     // get only first 3 topics
            //     topicsToSave.splice(9);
            // }
            await collection.insertMany(topicsToSave);
            console.log("Topics saved to database");
            // remove topics duplicated in trackedTopics
            trackedTopics = trackedTopics.filter(
                (t) =>
                    topicsToSave.findIndex((t2: WithId<Document>) =>
                        t2._id.equals(t._id)
                    ) === -1
            );
            let topicsToReturn = topicsToSave.concat(trackedTopics);

            //TO DO: remove this dedup Remove duplicates based on the 'id' property using inline functions
            topicsToReturn = topicsToReturn.filter(
                (item: any, index: number, self: any) =>
                    index === self.findIndex((t: any) => t._id === item._id)
            );
            res.setHeader("Content-Type", "application/json");
            res.setHeader("Cache-Control", "public, max-age=0");
            res.end(JSON.stringify(topicsToReturn));
        }
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
