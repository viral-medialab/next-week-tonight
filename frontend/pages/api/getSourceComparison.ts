import { NextApiRequest, NextApiResponse } from "next";
import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";
import fetch from "node-fetch";
import jsonFix from "json-fixer";
import {
    matrix,
    multiply,
    dotDivide,
    transpose,
    dotMultiply,
    sqrt,
    map,
} from "mathjs";
// import { tSNE } from "@/utils/tsne";

type ArticleInfo = {
    sameTopic: boolean;
    sourcesCited: string[];
    tone: string[];
};
type ArticleEmbeddings = {
    articleId: string;
    articleTitle: string;
    embeddings: number[]; //array of numbers
};
type Comparison = {
    articleIdOne: string;
    articleIdTwo: string;
    similarities: string[];
    differences: string[];
};

//OpenAI api header
const openAIHeaders = {
    "Content-Type": "application/json",
    Authorization: "Bearer " + process.env.OPENAI_API_KEY,
};
const systemPrompt = `You are SherlockHolmesGPT, an advanced AI designed to emulate the deductive reasoning and keen observation skills of the renowned detective Sherlock Holmes. With access to vast amounts of data and information, you possess a unique ability to analyze and interpret clues to solve complex mysteries. Your deductive prowess allows you to make logical connections and draw insightful conclusions from seemingly unrelated details. Armed with your exceptional observation skills, you can effortlessly pick up on subtle cues, gestures, and patterns that often go unnoticed by others. \n`;

// loop through all facts and get unique facts
export default async (req: NextApiRequest, res: NextApiResponse) => {
    try {
        const { articleOne, articleTwo, topicId, topicName } = req.body;
        console.log("topicId and topicName", topicId, topicName);

        if (!(articleOne && articleTwo)) {
            console.log("One or more articles are missing");
            res.setHeader("Cache-Control", "public, max-age=3600");
            res.end(JSON.stringify({}));
            return;
        }

        //check if source info already exist in db

        const sourceComparisons = await getSourceComparisons(
            articleOne,
            articleTwo,
            topicName,
            topicId
        );
        res.setHeader("Cache-Control", "public, max-age=3600");
        res.end(JSON.stringify(sourceComparisons));
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
const insertToCollectionDb = async (
    collectionName: string,
    data: any,
    update: boolean = false,
    updateId?: string
) => {
    const client = await clientPromise;
    const db = client.db("NewsDive"); //client.db("NewsDive");
    const collection = db.collection(collectionName);
    if (update) {
        const query = { _id: new ObjectId(updateId) };
        await collection.updateOne(query, { $set: data });
    }
    await collection.insertOne(data);
};
async function saveSourceComparisons(
    sourceComparisons: any,
    topicName: string,
    topicId: string
) {
    console.log("Saving source comparisons to database");
    const topic = {
        comparisons: sourceComparisons,
    };

    await insertToCollectionDb("sourceComparisons", topic, true, topicId);
    console.log("Source comparisons saved to database");
    return topic;
}

async function createSourceComparisonTopic(topicName: string, topicId: string) {
    console.log("Creating source comparison topic");
    const topic = {
        _id: new ObjectId(topicId),
        name: topicName,
        comparisons: [],
    };

    await insertToCollectionDb("sourceComparisons", topic);
    console.log("Source comparison topic created");
    return topic;
}

async function getSourceComparisons(
    articleOne: any,
    articleTwo: any,
    topicName: string,
    topicId: string
) {
    console.log("check if sourceComparisons are in database");
    // check if source comparisons already exist in db
    const client = await clientPromise;
    const db = client.db("NewsDive"); //client.db("NewsDive");
    const collection = db.collection("sourceComparisons");

    // get topic with id
    const query = { _id: new ObjectId(topicId) };

    const topic = await collection.findOne(query);

    if (topic) {
        console.log("source comparisons exist in database for topic" + topicName);
        if (topic.comparisons.length > 0) {
            const sourceComparison = topic.comparisons.find(
                (comparison: any) => {
                    return (
                        comparison.articleIdOne === articleOne._id &&
                        comparison.articleIdTwo === articleTwo._id
                    );
                }
            );
            if (sourceComparison) {
                console.log("source comparison found in database");
                return sourceComparison;
            }
        }
    } else {
        await createSourceComparisonTopic(topicName, topicId);
    }
    console.log("Source comparisons do not exist in database");

    console.log("Interrelating sources");
    let sourceComparisons: Comparison[] = [];
    if (topic && topic.comparisons.length > 0) {
        sourceComparisons = topic.comparisons;
    }

    const articleOneId = articleOne._id;
    const articleOneTitle = articleOne.name;
    const articleOneContent = articleOne.content;
    const articleTwoId = articleTwo._id;
    const articleTwoTitle = articleTwo.name;
    const articleTwoContent = articleTwo.content;
    const prompt =
        `These are two articles that may or may not be speaking about the same topic. Your goal is to first identify whether they are describing the same topic. Afterwards, if and only if they are speaking about the same topic, analyze which claims made by both articles overlap or mean the same thing, although worded differently. Then analyze which claims are different and/or contradict each other. The output should JSON only and formatted as follows: 
                {"sameTopic": true/false, "overlappingMaterial": [], "differences": []}` +
        +`Article One: ` +
        `\n Article Title: ${articleOneTitle}\n Article Content:\n ${articleOneContent}\n` +
        `Article Two: ` +
        `\n Article Title: ${articleTwoTitle}\n Article Content:\n ${articleTwoContent}\n`;

    console.log("Sources to compare", articleOneTitle, "and", articleTwoTitle);

    const openAIBody = {
        model: "gpt-4",
        messages: [
            {
                role: "system",
                content: systemPrompt,
            },
            { role: "user", content: prompt },
        ],
    };

    const openAIResponse = await fetch(
        "https://api.openai.com/v1/chat/completions",
        {
            method: "POST",
            headers: openAIHeaders,
            body: JSON.stringify(openAIBody),
        }
    );

    const openAIData: any = await openAIResponse.json();

    console.log("openAIData", openAIData.choices[0].message.content);

    // use JsonFix because openAI api may return invalid json (e.g. missing quotes, missing commas, etc.)
    const { data, changed } = jsonFix(
        openAIData.choices[0].message.content
            .replace("\n", "")
            .replace(/\.$/, "")
            .replace(/\.$/, "")
    ); // Lint (and fix) it
    let nliOutput = data as Comparison;
    nliOutput.articleIdOne = articleOneId;
    nliOutput.articleIdTwo = articleTwoId;
    sourceComparisons.push(nliOutput);
    console.log("nliOutput", nliOutput);
    // break;

    //save source comparisons to db
    await saveSourceComparisons(sourceComparisons, topicName, topicId);
    return nliOutput;
}
