import { NextApiRequest, NextApiResponse } from "next";
import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";
// loop through all facts and get unique facts
export default async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        const { topicsAndArticles: articlesDoc } = req.body;
        // console.log("topicsAndArticles", topicAndArticles);

        //check if source info already exist in db
        const topicId: string = articlesDoc._id; //topic id
        const topicName: string = articlesDoc.topic; //topic name

        const sourceInfo = articlesDoc.articles; // articles have source info and tone

        // get source embeddings
        let sourceEmbeddings;
        let embeddingSimilarities;
        const client = await clientPromise;
        const db = client.db("NewsDive"); //client.db("NewsDive");
        const collection = db.collection("sourceEmbeddings");
        // get topic with id

        const query = { _id: new ObjectId(topicId) };

        const topic = await collection.findOne(query);

        if (topic) {
            console.log("source embeddings exist in database");
            sourceEmbeddings = topic.embeddings;
            embeddingSimilarities = topic.similarities;
        } else {
            console.log("source embeddings do not exist in database");
            throw new Error("source embeddings do not exist in database");
        }

        const dataToReturn = {
            _id: topicId,
            topic: topicName,
            sourceInfo: sourceInfo,
            sourceEmbeddings: sourceEmbeddings,
            embeddingSimilarities: embeddingSimilarities,
        };

        res.setHeader("Cache-Control", "public, max-age=3600");
        res.status(200).end(JSON.stringify(dataToReturn));
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
