import clientPromise from "@/lib/mongodb";
import { WithId, Document } from "mongodb";
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

const WEEKS_THRESHOLD = 1; // Configure this to change the time frame

export default async (req: NextApiRequest, res: NextApiResponse) => {
    const headers = {
        "Ocp-Apim-Subscription-Key": process.env.BING_NEWS_API_KEY || "",
    };

    try {
        console.log("Checking if topics exist in database");
        const client = await clientPromise;
        const db = client.db("news");
        const trendingTopics = db.collection("trendingTopics");
        const host = "http://" + req.headers.host;
        const isDebug = false;

        const today = new Date();
        const cutoffDate = new Date(today.getTime() - WEEKS_THRESHOLD * 7 * 24 * 60 * 60 * 1000);
        
        console.log("Current host name: " + host);
        console.log("Cutoff date: " + cutoffDate.toISOString());

        // Find topics with recent articles
        const recentTopics = await trendingTopics.find({
            "articles": {
                $elemMatch: {
                    "date_published": { $gte: cutoffDate }
                }
            }
        }).toArray();

        console.log("Recent topics found: " + recentTopics.length);

        const trackedTopicsQuery = {
            $or: [{ isTrackedTopic: true }, { isPinnedTopic: true }],
        };
        let trackedTopics = await trendingTopics.find(trackedTopicsQuery).toArray();

        if (recentTopics.length > 0) {
            // Filter articles within each topic
            const filteredTopics = recentTopics.map(topic => ({
                ...topic,
                articles: topic.articles.filter((article: any) => 
                    new Date(article.date_published) >= cutoffDate
                )
            }));

            console.log("Topics with recent articles: " + filteredTopics.length);

            // Combine filtered topics with tracked topics
            let topicsToReturn = filteredTopics.concat(trackedTopics);

            // Remove duplicates
            topicsToReturn = topicsToReturn.filter(
                (item: any, index: number, self: any) =>
                    index === self.findIndex((t: any) => t._id.toString() === item._id.toString())
            );

            res.setHeader("Content-Type", "application/json");
            res.setHeader("Cache-Control", "public, max-age=0");
            res.end(JSON.stringify(topicsToReturn));
            return;
        } else {
            console.log("No recent topics found, fetching new ones");
            const topics = await fetch(host + "/api/createNewsTopics");
            const topicsData: any = await topics.json();
            const topicsDataArray = topicsData
                .replace(/[\[\]"]+/g, "")
                .split(",")
                .map((topic: string) => topic.trim());
            
            console.log("Saving topics to database");
            const topicsToSave = topicsDataArray.map((topic: string) => ({
                topic: topic,
                date: today.toISOString().split('T')[0],
                createdAt: new Date(),
                isArticlesProcessed: false,
                isTrackedTopic: false,
                isPinnedTopic: false,
            }));

            if (isDebug) {
                topicsToSave.splice(9);
            }

            await trendingTopics.insertMany(topicsToSave);
            console.log("Topics saved to database");

            // Remove topics duplicated in trackedTopics
            trackedTopics = trackedTopics.filter(
                (t) =>
                    topicsToSave.findIndex((t2: WithId<Document>) =>
                        t2._id.equals(t._id)
                    ) === -1
            );

            let topicsToReturn = topicsToSave.concat(trackedTopics);

            // Remove duplicates
            topicsToReturn = topicsToReturn.filter(
                (item: any, index: number, self: any) =>
                    index === self.findIndex((t: any) => t._id.toString() === item._id.toString())
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