import clientPromise from "@/lib/mongodb";
import { Filter, ObjectId } from "mongodb";
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

/**
 * Retrieves a topic by ID from the MongoDB database.
 * If the topic exists, it returns the topic.
 * If the topic does not exist, it returns a 404 error.
 * If there is an error, it returns a 500 error.
 * @param {NextApiRequest} req - The Next.js API request object.
 * @param {NextApiResponse} res - The Next.js API response object.
 * @returns {Promise<void>} - A promise that resolves when the response is sent.
 */
export default async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        console.log("Checking if articles exist in database");
        //get id from req
        const { topicId: id }: { topicId: string } = req.body;
        const { topicsAndArticles: topicAndArticles } = req.body;
        const { id: string } = req.body;
        const client = await clientPromise;
        const db = client.db("news"); //client.db("NewsDive");
        const articlesCollection = db.collection("trendingTopics");
        // get topic with id

        const query = { _id: new ObjectId(id) };
        console.log("looking for topic: ", query);
        const topic = await articlesCollection.findOne(query);
        if (topic) {
            console.log(
                "Articles exist in database under topic: " + topic.topic
            );
            res.status(200);
            res.end(JSON.stringify(topic));
        } else {
            console.log("Articles do not exist in database for topic");
            res.status(404).end();
            return;
        }
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
