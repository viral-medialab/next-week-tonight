const { connectToMongo } = require("./mongoClient");

const getTopics = async (db) => {
    //set api header

    console.log("Checking if topics exist in database");
    // Checking if topics exist in mongodb database
    // if topics exist, return topics
    // if topics do not exist, get topics from bing news api
    const collection = db.collection("topics");
    // get topics for today
    const today = new Date();
    const date =
        today.getFullYear() +
        "-" +
        (today.getMonth() + 1) +
        "-" +
        today.getDate();

    const query = { date: date };
    const topics = await collection.find(query).toArray();

    const trackedTopicsQuery = {
        $or: [{ isTrackedTopic: true }, { isPinnedTopic: true }],
    };
    let trackedTopics = await collection.find(trackedTopicsQuery).toArray();

    if (topics.length > 0) {
        console.log("Topics exist in database");
        // remove topics duplicated in trackedTopics
        trackedTopics = trackedTopics.filter(
            (t) => topics.findIndex((t2) => t2._id.equals(t._id)) === -1
        );
        // topicsToReturn should be the union of topics and trackedTopics but remove the duplicates
        let topicsToReturn = topics.concat(trackedTopics);

        console.log("topicsToReturn", topicsToReturn);
        return topicsToReturn;
    } else {
        console.log("Topics do not exist in database");
        // call createNewsTopics api
        // save topics to mongodb database
        const topics = await createTopics();
        const topicsDataArray = topics
            .replace(/[\[\]"]+/g, "")
            .split(",")
            .map((topic) => topic.trim()).slice(0,8);
        console.log("Saving topics to database");
        const topicsToSave = topicsDataArray.map((topic) => ({
            topic: topic,
            date: date,
            createdAt: new Date(),
            isArticlesProcessed: false,
            isTrackedTopic: false,
            isPinnedTopic: false,
        }));
        await collection.insertMany(topicsToSave);
        console.log("Topics saved to database");
        // remove topics duplicated in trackedTopics
        trackedTopics = trackedTopics.filter(
            (t) => topicsToSave.findIndex((t2) => t2._id.equals(t._id)) === -1
        );
        // topicsToReturn should be the union of topics and trackedTopics but remove the duplicates
        let topicsToReturn = topicsToSave.concat(trackedTopics);

        return topicsToReturn;
    }
};

const createTopics = async () => {
    const url = process.env.BING_NEWS_ENDPOINT + "?q=&mkt=en-us";

    //Bing News api header
    const newsHeaders = {
        "Ocp-Apim-Subscription-Key": process.env.BING_NEWS_API_KEY || "",
    };

    console.log("Now getting news");

    const newsResponse = await fetch(url, { headers: newsHeaders });
    const newsData = await newsResponse.json();
    console.log(newsData);

    //get topics from headlines in newsData
    //OpenAI api header
    console.log("Now getting topics backend");
    const openAIHeaders = {
        "Content-Type": "application/json",
        Authorization: "Bearer " + process.env.OPENAI_API_KEY,
    };

    //prompt
    const newsHeadlines = newsData.value.map((article) => ({
        title: article.name,
        description: article.description,
    }));

    const topicPrompt =
        `Return a comprensive list of unique topics covered by these news headlines and descriptions. These topics will be used by a news API to get even more articles on the particular topic. Please provide specific topics. It is essential the topics do not overlap with each other and are unique, that is, do not be repetitive. Format the response as an array of topics. For example, ["Pakistani's defeat in war against Iraq", "New York Marathon", "US Senate elections"]. Use enough descriptive words (up to 7 words) to make the topic specific enough and captilize the first letter. Do not miscategorize topics, for example: if the topic is "Convicted Felon arrested for illegal weapons in Washington", do not miscategorize it as "Washington Senator convicted for illegal weapons". Remain true to the topic at hand. Do not use commas in the topics to avoid ambiguity with the array commas. Do not return anything else except the array.\n` +
        `News headlines and descriptions:\n` +
        newsHeadlines
            .map(
                (article, idx) =>
                    `Article ${idx + 1}\n Headline: ${
                        article.title
                    }\n Description: ${article.description}\n`
            )
            .join("\n");

    //OpenAI api body
    const openAIBody = {
        model: "gpt-3.5-turbo",
        messages: [
            { role: "system", content: "You are a helpful assistant." },
            { role: "user", content: topicPrompt },
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
    console.log("openAIData", openAIData.choices[0].message);

    const topics = openAIData.choices[0].message.content.replace("\n", "");
    return topics;
};

module.exports = { getTopics };
