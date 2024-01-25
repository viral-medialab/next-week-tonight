
import { NextApiRequest, NextApiResponse } from "next";
import fetch from "node-fetch";

export default async (req: NextApiRequest, res: NextApiResponse) => {
    const url = process.env.BING_NEWS_ENDPOINT + "?q=&mkt=en-us";

    //Bing News api header
    const newsHeaders = {
        "Ocp-Apim-Subscription-Key": process.env.BING_NEWS_API_KEY || "",
    };

    try {
        console.log("Now getting news");

        const newsResponse = await fetch(url, { headers: newsHeaders });
        const newsData: any = await newsResponse.json();
        console.log(newsData);

        //get topics from headlines in newsData
        //OpenAI api header
        console.log("Now getting topics frontend");
        const openAIHeaders = {
            "Content-Type": "application/json",
            Authorization: "Bearer " + process.env.OPENAI_API_KEY,
        };

        //prompt
        const newsHeadlines = newsData.value.map((article: any) => ({
            title: article.name,
            description: article.description,
        }));

        const numTopics = 8;

        const topicPrompt =
            `Return a comprensive list of ${numTopics} unique topics covered by these news headlines and descriptions. These topics will be used by a news API to get even more articles on the particular topic. Please provide specific topics. It is essential the topics do not overlap with each other and are unique, that is, do not be repetitive. Format the response as an array of topics. For example, ["Pakistani's defeat in war against Iraq", "New York Marathon", "US Senate elections"]. Use enough descriptive words (up to 7 words) to make the topic specific enough. Do not use commas in the topics to avoid ambiguity with the array commas. Do not return anything else except the array.\n` +
            `News headlines and descriptions:\n` +
            newsHeadlines
                .map(
                    (article: any, idx: number) =>
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
        const openAIData: any = await openAIResponse.json();
        console.log("openAIData", openAIData.choices[0].message);
        //limit - 5 topics for debugging 
        const topics = openAIData.choices[0].message.content.replace("\n", "");

        res.setHeader("Cache-Control", "public, max-age=3600");
        res.end(JSON.stringify(topics));
    } catch (error) {
        console.error(error);
        res.status(500).end();
    }
};
