const { ObjectId } = require("mongodb");
const Fuse = require("fuse.js");
const jsonFix = require("json-fixer");
// loop through all facts and get unique facts
const getFacts = async (db, topic, articles) => {
    // Get facts from openAI
    const topicId = topic._id; //topic id
    const topicName = topic.topic; //topic name
    const query = { _id: new ObjectId(topicId) };
    console.log("articles in getFacts", articles);
    console.log("check if temp facts exist in db");
    const tempFactsCollection = db.collection("tempFacts");
    const tempTopic = await tempFactsCollection.findOne(query);
    let allFacts;
    if (tempTopic) {
        console.log("Temp facts exist in database");
        allFacts = tempTopic.facts;
        if (allFacts.length === 0) {
            allFacts = getAllFacts(articles, topicName);
            await tempSaveFactsAndSources(db, allFacts, topicName, topicId);
        }
        console.log("allFacts", allFacts)
        console.log("tempTopic", tempTopic)
        console.log("tempTopic.facts", tempTopic.facts)
    } else {
        console.log("Temp facts do not exist in database, getting facts");
        allFacts = await getAllFacts(articles, topicName);
        await tempSaveFactsAndSources(db, allFacts, topicName, topicId);
    }

    console.log("check if unique facts exist in db");
    const uniqueFactsCollection = db.collection("facts");
    const uniqueTopic = await uniqueFactsCollection.findOne(query);
    if (uniqueTopic) {
        console.log("Unique facts exist in database");
        topic = uniqueTopic;
    } else {
        console.log(
            "Unique facts do not exist in database, getting unique facts",
            allFacts.length
        );
        //filter all facts to only include unique facts
        const uniqueFacts = await getUniqueFacts(allFacts);
        topic = await saveFactsAndSources(db, uniqueFacts, topicName, topicId);
    }
};

//OpenAI api header
const openAIHeaders = {
    "Content-Type": "application/json",
    Authorization: "Bearer " + process.env.OPENAI_API_KEY,
};
const systemPrompt = `You are SherlockHolmesGPT, an advanced AI designed to emulate the deductive reasoning and keen observation skills of the renowned detective Sherlock Holmes. With access to vast amounts of data and information, you possess a unique ability to analyze and interpret clues to solve complex mysteries. Your deductive prowess allows you to make logical connections and draw insightful conclusions from seemingly unrelated details. Armed with your exceptional observation skills, you can effortlessly pick up on subtle cues, gestures, and patterns that often go unnoticed by others. \n`;

const getAllFacts = async (articles, topicName) => {
    console.log("Getting all facts");
    // loop through all articles and get facts for each
    let factsPrompt = `Return a comprehensive list of all the unique hypotheses, claims and statistics about the topic: ${topicName} that the content below contains. Note, each hypothesis should be independent and be able to read individually without the context of the other hypotheses, that is, do not use any pronouns or words that refer back to other hypotheses. Make the hypotheses as conjectures that could be inferred from reading the content. For example, if the article states critics say happiness may be linked to socioeconomic status then the resulting hypothesis that can be inferred is "happiness is linked to socioeconomic status." If the article states, "Scientists claim the world has 30 years left before it ends" then the inferred conjecture is "The world has 30 years left." Notice I left out "scientists said." If the article states "it is interpreted that cofounder Sergey Brin is worried about losing his money" then the inferred conjecture is "Sergey Brin is worried about losing his money." Notice I didn’t use the words "interpreted." Also do not use hedge words like "may, might, possibly, etc." Instead, use assertive language. In  addition, quote verbatim the excerpt where the claim was made. Your output should be only JSON formatted as follows: 
    {"hypotheses": [{"claim": "", "citation": ""}, … ]}`;
    const allFacts = []; //array of objects, each object is a set of facts

    const fetchPromises = articles.map(async (article) => {
        const articleId = article._id;
        const articleTitle = article.name;
        const articleContent = article.content.substring(0,Math.min(article.content.length, 15000));
        console.log("Getting facts for article: " + articleTitle);
        maxPromptLength = 16000;
        const promptToUse =
            factsPrompt +
            `\n Article Title: ${articleTitle}\n Article Content:\n ${articleContent}\n`;


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

        return fetch("https://api.openai.com/v1/chat/completions", {
            method: "POST",
            headers: openAIHeaders,
            body: JSON.stringify(openAIBody),
        })
        .then(res => res.json())
        .then(openAIData => {
            console.log("openAIData", openAIData);
            console.log("openAIData facts", openAIData.choices[0].message.content);
            let curFacts = JSON.parse(
                openAIData.choices[0].message.content.replace("\n", "").replace(/\.$/, "")
            );
            curFacts.articleId = articleId;
            curFacts.articleTitle = articleTitle;
            return curFacts;
        })
        .catch(error => {
            console.error(error);
        });

    });

    const results = await Promise.all(fetchPromises);
    results.forEach(result => {
        if (result) {
            allFacts.push(result);
        }
    });

    console.log("debug: allFacts", allFacts.length);
    console.log("Completed: getAllFacts");
    return allFacts;
}


    // for (let i = 0; i < articles.length; i++) {
    //     try {
    //         const article = articles[i];
    //         const articleId = article._id;
    //         const articleTitle = article.name;
    //         const articleContent = article.content;
    //         console.log("Getting facts for article: " + articleTitle);

    //         const promptToUse =
    //             factsPrompt +
    //             `\n Article Title: ${articleTitle}\n Article Content:\n ${articleContent}\n`;

    //         //OpenAI api body
    //         const openAIBody = {
    //             model: "gpt-4",
    //             messages: [
    //                 {
    //                     role: "system",
    //                     content: systemPrompt,
    //                 },
    //                 { role: "user", content: promptToUse },
    //             ],
    //         };

    //         const openAIResponse = await fetch(
    //             "https://api.openai.com/v1/chat/completions",
    //             {
    //                 method: "POST",
    //                 headers: openAIHeaders,
    //                 body: JSON.stringify(openAIBody),
    //             }
    //         );

    //         const openAIData = await openAIResponse.json();

    //         console.log("openAIData", openAIData);

    //         console.log(
    //             "openAIData facts",
    //             openAIData.choices[0].message.content
    //         );
    //         let curFacts = JSON.parse(
    //             openAIData.choices[0].message.content
    //                 .replace("\n", "")
    //                 .replace(/\.$/, "")
    //         ); //array of facts
    //         curFacts.articleId = articleId;
    //         curFacts.articleTitle = articleTitle;

    //         allFacts.push(curFacts);
    //     } catch (error) {
    //         console.error(error);
    //         continue;
    //     }
    // }
    // console.log("debug: allFacts", allFacts.length);
    // return allFacts;
// };

const getUniqueFacts = async (allFacts) => {
    if (allFacts.length > 0 && allFacts[0].hypotheses && Array.isArray(allFacts[0].hypotheses)) {

        console.log("Getting unique facts", allFacts);
        // loop through all facts and get unique facts
        const formattedFacts = allFacts.map((fact) => {
            if (fact.hypotheses && Array.isArray(fact.hypotheses)) {
                return fact.hypotheses.map((hypothesis) => {
                    return {
                        claim: hypothesis.claim,
                        sources: [  
                            {
                                citation: hypothesis.citation,
                                articleId: fact.articleId,
                            },
                        ],
                    };
                });
            }
            else {
                return []; 
            }

        });

        
        if (!formattedFacts || !Array.isArray(formattedFacts)) {
            console.log("Formatted facts", formattedFacts);
            return [];
        }

        if (formattedFacts.length === 0){
            console.log("formatted facts length 0", formattedFacts);
            return [];
        }

        console.log(
            "formatted facts debug",
            //formattedFacts,
            formattedFacts.length,
            //allFacts[0].hypotheses,
        );
    

        let currentFacts = formattedFacts[0];
        for (let i = 1; i < formattedFacts.length; i++) {
            try {
                console.log("comparing facts");
                console.log("currentFacts ", currentFacts);
                console.log("sourceTwo ", i, formattedFacts[i]);
                const factsToCompare = JSON.stringify({
                    sourceOne: currentFacts.map((fact) => ({
                        claim: fact.claim,
                    })),
                    sourceTwo: formattedFacts[i].map((fact) => ({
                        claim: fact.claim,
                    })), // remove source/articleId
                });
                console.log("factsToCompare", factsToCompare);
                const prompt =
                    `Here are two sets of claims made from two different sources about the same topic. You are required to eliminate the redundancy between these claims if any exist. Specifically, if two claims from both articles are essentially equivalent, although have been worded differently, you should rewrite the claim and cite verbatim the two claims. If a claim in one article is not shared by the other article it should be returned with only one citation. Your output should be only JSON formatted as follows: 
            {"hypotheses": [ {"claim": "", "claimUsedFromSourceOne": "", "claimUsedFromSourceTwo": ""}, … ]}\nFacts to compare:\n` +
                    factsToCompare;
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

                const openAIData = await openAIResponse.json();

                console.log("openAIData", openAIData.choices[0].message.content);

                // use JsonFix because openAI api may return invalid json (e.g. missing quotes, missing commas, etc.)
                const { data, changed } = jsonFix(
                    openAIData.choices[0].message.content
                        .replace("\n", "")
                        .replace(/\.$/, "")
                ); // Lint (and fix) it
                let processedFacts = data;
                const newCurrentFacts = [];
                processedFacts.hypotheses.forEach((fact) => {
                    const fuseOptions = {
                        shouldSort: true,
                        keys: ["claim"],
                    };
                    const sources = [];
                    if (fact.claimUsedFromSourceOne) {
                        const fuse = new Fuse(currentFacts, fuseOptions);
                        const searchResults = fuse.search(
                            fact.claimUsedFromSourceOne
                        );

                        const claimSourceOneSources =
                            searchResults[0]?.item.sources; // get sources from first search result

                        if (!claimSourceOneSources)
                            throw new Error(
                                "1. No sources found for fact: " + fact
                            );

                        console.log(
                            "found sources for fact",
                            fact.claim,
                            claimSourceOneSources
                        );
                        // push all sources in claimSourceOneSources to sources in one line without for loop
                        sources.push(...claimSourceOneSources);
                    }
                    if (fact.claimUsedFromSourceTwo) {
                        const fuse = new Fuse(formattedFacts[i], fuseOptions);
                        const searchResults = fuse.search(
                            fact.claimUsedFromSourceTwo
                        );

                        const claimSourceTwoSources =
                            searchResults[0]?.item.sources; // get sources from first search result

                        if (!claimSourceTwoSources)
                            throw new Error(
                                "2. No sources found for fact: " + fact
                            );
                        console.log(
                            "found sources for fact",
                            fact.claim,
                            claimSourceTwoSources
                        );
                        sources.push(...claimSourceTwoSources);
                    }
                    if (sources) {
                        newCurrentFacts.push({
                            claim: fact.claim,
                            sources: sources,
                        });
                    } else {
                        throw new Error("3. No sources found for fact: " + fact);
                    }
                });

                currentFacts = newCurrentFacts;
                console.log("currentFacts", currentFacts);
            } catch (error) {
                console.error(error);
                continue;
            }
        }
    
        return currentFacts.map((fact) => ({ ...fact, _id: new ObjectId() })); // make sure each fact has an id
    }
};

const saveFactsAndSources = async (db, facts, topicName, topicId) => {
    console.log("Saving facts and sources to database");
    const collection = db.collection("facts");
    const topic = {
        _id: new ObjectId(topicId),
        topic: topicName,
        facts: facts,
    };
    await collection.insertOne(topic);
    console.log("Facts and sources saved to database");
    return topic;
};

const insertToCollectionDb = async (db, collectionName, data) => {
    const collection = db.collection(collectionName);
    await collection.insertOne(data);
};

async function tempSaveFactsAndSources(db, facts, topicName, topicId) {
    console.log("Temp saving facts and sources to database");

    const topic = {
        _id: new ObjectId(topicId),
        topic: topicName,
        facts: facts,
    };
    await insertToCollectionDb(db, "tempFacts", topic);
    console.log("Temp facts and sources saved to database");
}

module.exports = { getFacts };
