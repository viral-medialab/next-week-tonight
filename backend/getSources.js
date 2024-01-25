const { ObjectId } = require("mongodb");
const jsonFix = require("json-fixer");
const { matrix, multiply, dotDivide, transpose, sqrt, map } = require("mathjs");
// import { tSNE } from "@/utils/tsne";

//OpenAI api header
const openAIHeaders = {
    "Content-Type": "application/json",
    Authorization: "Bearer " + process.env.OPENAI_API_KEY,
};
const systemPrompt = `You are SherlockHolmesGPT, an advanced AI designed to emulate the deductive reasoning and keen observation skills of the renowned detective Sherlock Holmes. With access to vast amounts of data and information, you possess a unique ability to analyze and interpret clues to solve complex mysteries. Your deductive prowess allows you to make logical connections and draw insightful conclusions from seemingly unrelated details. Armed with your exceptional observation skills, you can effortlessly pick up on subtle cues, gestures, and patterns that often go unnoticed by others. \n`;

// loop through all facts and get unique facts
const getSources = async (db, articlesDoc) => {
    // console.log("topicsAndArticles", topicAndArticles);

    if (articlesDoc.articles.length === 0) {
        console.log("No articles to process");
        return [];
    }

    //check if source info already exist in db
    const topicId = articlesDoc._id; //topic id

    await getSourceInfo(db, articlesDoc);

    // get source embeddings
    const sourceEmbeddings = await getSourceEmbeddings(db, articlesDoc);

    // get embedding similarities
    await getEmbeddingSimilarities(db, sourceEmbeddings, topicId);
};

const insertToCollectionDb = async (
    db,
    collectionName,
    data,
    update = false,
    updateId
) => {
    const collection = db.collection(collectionName);
    if (update) {
        const query = { _id: new ObjectId(updateId) };
        await collection.updateOne(query, { $set: data });
    }
    await collection.insertOne(data);
};

async function saveSourceInfo(db, articlesDoc, topicId) {
    console.log("Saving sources information to database");
    const dataToSave = {
        articles: articlesDoc.articles,
    };

    await insertToCollectionDb(db, "articles", dataToSave, true, topicId);
    console.log("Sources information saved to database");
    return dataToSave;
}
const getSourceInfo = async (db, articlesDoc) => {
    console.log("Getting sources information ");
    const topicId = articlesDoc._id; //topic id
    // loop through all articles and get source info for each
    let sourceInfoPrompt = `Your job is to analyze this article for specific details. First, cite all the sources that the authors explicitly use for information including people whose direct quotes are used, organizations, literature or well known theories. Also, analyze the tone of the author, are they formal or informal, optimistic or pessimistic, enthusiastic or calm, apathetic or impassioned, serious or humorous, sarcastic or sincere, intimate or detached. Use any words you see fit to describe their tone most appropriately. Your output should be only JSON formatted as follows:
    {"sourcesCited": [], "tone": ""}\n`;
    for (let i = 0; i < articlesDoc.articles.length; i++) {
        try {
            const article = articlesDoc.articles[i];
            const articleTitle = article.name;
            const articleContent = article.content;
            console.log(
                "Getting source information for article: " + articleTitle
            );

            const promptToUse =
                sourceInfoPrompt +
                `\n Article Title: ${articleTitle}\n Article Content:\n ${articleContent}\n`;
            //OpenAI api body
            const openAIBody = {
                model: "gpt-4",
                messages: [
                    {
                        role: "system",
                        content: systemPrompt,
                    },
                    { role: "user", content: promptToUse },
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

            const openAIData = await openAIResponse.json();

            console.log("openAIData", openAIData.choices[0].message.content);
            const { data, changed } = jsonFix(
                openAIData.choices[0].message.content
                    .replace("\n", "")
                    .replace(/\.$/, "")
            );
            let curFacts = data; //array of facts

            articlesDoc.articles[i] = {
                ...articlesDoc.articles[i],
                ...curFacts,
            };
        } catch (error) {
            console.log("error", error);
            continue;
        }
    }
    await saveSourceInfo(db, articlesDoc, topicId);
    return articlesDoc.articles;
};

async function saveSourceEmbeddings(db, embeddings, topicName, topicId) {
    console.log("Saving article embeddings to database");
    const dataToSave = {
        _id: new ObjectId(topicId),
        topic: topicName,
        embeddings: embeddings,
    };

    await insertToCollectionDb(db, "sourceEmbeddings", dataToSave);
    console.log("article embeddings saved to database");
    return dataToSave;
}

async function getSourceEmbeddings(db, articlesDoc) {
    // check if source comparisons already exist in db
    const topicName = articlesDoc.topic; //topic name
    const topicId = articlesDoc._id; //topic id

    console.log("getting embeddings of sources");
    // loop through all articles and get embeddings for each
    // let factsPrompt = `Return a comprehensive list of all the unique hypotheses, claims and statistics about the topic: ${topicTitle} that the content below contains. Note, each hypothesis should be independent and be able to read individually without the context of the other hypotheses, that is, do not use any pronouns or words that refer back to other hypotheses. Make the hypotheses as conjectures that could be inferred from reading the content. For example, if the article states critics say happiness may be linked to socioeconomic status then the resulting hypothesis that can be inferred is "happiness is linked to socioeconomic status." If the article states, "Scientists claim the world has 30 years left before it ends" then the inferred conjecture is "The world has 30 years left." Notice I left out "scientists said." If the article states "it is interpreted that cofounder Sergey Brin is worried about losing his money" then the inferred conjecture is "Sergey Brin is worried about losing his money." Notice I didn’t use the words "interpreted." Also do not use hedge words like "may, might, possibly, etc." Instead, use assertive language. In  addition, quote verbatim the excerpt where the claim was made. The output format is JSON and should follow this template:
    // {"hypotheses": [ {"claim": "", "citation": ""}, … ],  "statistics": [ {"stat": "", citation: ""}]}`;
    const sourceEmbeddings = []; //array of objects, each object is a set of facts
    for (let i = 0; i < articlesDoc.articles.length; i++) {
        try {
            const article = articlesDoc.articles[i];
            const articleId = article._id;
            const articleTitle = article.name;
            const articleContent = article.content;
            console.log("Getting embeddings for article: " + articleTitle);

            //replace all html tags with empty string
            const promptToUse = articleContent.replace(/<.*?>/g, "") + "\n";

            //OpenAI api body
            const openAIBody = {
                model: "text-embedding-ada-002",
                input: promptToUse,
            };

            const openAIResponse = await fetch(
                "https://api.openai.com/v1/embeddings",
                {
                    method: "POST",
                    headers: openAIHeaders,
                    body: JSON.stringify(openAIBody),
                }
            );

            const openAIData = await openAIResponse.json();
            console.log("length of data", openAIData.data.length);
            console.log("openAIData", openAIData.data[0].embedding);
            const curEmbeddings = {
                articleId: articleId,
                articleTitle: articleTitle,
                embeddings: openAIData.data[0].embedding,
            };
            sourceEmbeddings.push(curEmbeddings);
            // break;
        } catch (error) {
            console.log("error", error);
            continue;
        }
    }
    //save source comparisons to db
    await saveSourceEmbeddings(db, sourceEmbeddings, topicName, topicId);
    return sourceEmbeddings;
}

async function saveEmbeddingSimilarities(db, similarities, _id) {
    console.log("Saving embedding similarities to database");
    const dataToSave = {
        similarities: similarities,
    };

    await insertToCollectionDb(db, "sourceEmbeddings", dataToSave, true, _id);
    console.log("Embedding similarities saved to database");
    return dataToSave;
}

async function getEmbeddingSimilarities(db, sourceEmbeddings, topicId) {
    //check if similarities already exist in db
    console.log("Getting embedding similarities");
    const embeddingsMatrix = matrix(
        sourceEmbeddings.map((embedding) => embedding.embeddings)
    );
    const embeddingsNorm = map(
        multiply(embeddingsMatrix, transpose(embeddingsMatrix)),
        sqrt
    ); //norm of each embedding
    const embeddingsDotProd = multiply(
        embeddingsMatrix,
        transpose(embeddingsMatrix)
    ); //dot product of each embedding

    const similarities = dotDivide(embeddingsDotProd, embeddingsNorm);
    console.log("embeddingsMatrix shape", embeddingsMatrix.size());
    console.log("embeddingsNorm shape", embeddingsNorm.size());
    console.log("embeddingsDotProd shape", embeddingsDotProd.size());
    console.log("similarities shape", similarities.size());
    const dists = similarities.toArray();

    //save similarities and tSNE coordinates to db
    await saveEmbeddingSimilarities(db, dists, topicId);

    return dists;
}

module.exports = { getSources };
