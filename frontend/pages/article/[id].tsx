import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";
import ChatCopy from "@/components/ChatCopy";

export default function Article({}: {}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [articleContents, setArticleContents] = useState<string | null>(null);
  const [articleTitle, setArticleTitle] = useState<string | null>(null);
  const [sidebarPredictions, setSidebarPredictions] = useState<string[]>([]);
  const [updateTrigger, setUpdateTrigger] = useState<number>(0);

  const router = useRouter();
  const { id: urlID } = router.query; // Retrieve urlID from the current address

  useEffect(() => {
    const fetchArticleInfo = async () => {
      if (urlID) {
        try {
          const response = await fetch("https://backend-next-week-tonight-a073583ba0cf.herokuapp.com/api/gather_article_info", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              article_id: urlID,
            }),
          });
  
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
  
          const data = await response.json();
          setArticleTitle(data["title"]);
          // Original content
          let contents = data["contents"];
  
          // Check if there are sources to format
          if (contents.includes('Sources:')) {
            const [content, rawSources] = contents.split('Sources: ');
            const formattedSources = rawSources
              .match(/\(\d+\) (https?:\/\/[^\s]+)/g)
              .map((source, index) => {
                const url = source.match(/https?:\/\/[^\s]+/)[0];
                return `<a href="${url}" target="_blank" rel="noopener noreferrer">(Source ${index + 1}) ${url}</a>`;
              })
              .join('<br>');
  
            // Combine the content and formatted sources with line breaks in between
            contents = `${content}<br><br>Sources:<br>${formattedSources}`;
          }
  
          // Set the formatted article contents
          setArticleContents(contents);
        } catch (error) {
          console.error("Error fetching article info:", error);
        }
      }
    };
  
    fetchArticleInfo();
  }, [urlID]);
  
  const handleToggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleBackButtonClick = () => {
    router.back();
  };

  const notifyArticleUpdate = () => {
    // Incrementing the updateTrigger will trigger the useEffect
    setUpdateTrigger((prev) => prev + 1);
  };

  const Sidebar: React.FC<{ currentArticleTitle: string; predictions: string[] }> = ({
    currentArticleTitle,
    predictions,
  }) => {
    const [predictionNames, setPredictionNames] = useState<string[]>([]);
    const router = useRouter();
    const { id: urlID } = router.query;

    const handleClearCache = async () => {
      try {
        console.log(urlID);
        if (urlID) {
          const response = await fetch("https://backend-next-week-tonight-a073583ba0cf.herokuapp.com/api/handle_clear_cache", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              article_id: urlID,
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          notifyArticleUpdate();
        } else {
          console.error("urlID is not defined.");
        }
      } catch (error) {
        console.error("Error clearing cache:", error);
      }
    };

    useEffect(() => {
      const fetchPredictionNames = async () => {
        try {
          const promises = predictions.map(async (prediction) => {
            const response = await fetch("https://backend-next-week-tonight-a073583ba0cf.herokuapp.com/api/gather_article_info", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                article_id: prediction,
              }),
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data["title"];
          });

          const names = await Promise.all(promises);
          setPredictionNames(names);
        } catch (error) {
          console.error("Error fetching prediction names:", error);
        }
      };

      if (predictions && predictions.length > 0) {
        fetchPredictionNames();
      }
    }, [predictions]);

    return (
      <div className="w-1/5 bg-gray-200 p-4 m-4 max-h-full overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Navigation</h2>
        <button onClick={handleClearCache} className="text-blue-700 hover:underline">
                Clear Cache
        </button>
        <ul>
          <li className="mb-2">
            <a href="" target="_self" rel="noopener noreferrer">
              {currentArticleTitle}
            </a>
          </li>
        </ul>
        {predictionNames && predictionNames.map((name, index) => (
          <div key={index}>
          <a href={`/article/${predictions[index]}`} key={index}>
            <p> ↳ {name}</p>
          </a>
          {index < predictionNames.length - 1 && <div style={{ height: "8px" }} />}
          </div>
        ))}
      </div>
    );
  };

  useEffect(() => {
    const updateSidebarPredictions = async () => {
      try {
        const response = await fetch("https://backend-next-week-tonight-a073583ba0cf.herokuapp.com/api/gather_article_info", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            article_id: urlID,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Data for Children Articles", data);
        setSidebarPredictions(data["children"]);
      } catch (error) {
        console.error("Error fetching article info:", error);
      }
    };

    updateSidebarPredictions();
  }, [updateTrigger, urlID]);

  return (
    <div className="container mx-auto px-4 py-8 flex-col">
      <div className="flex">
        <Sidebar currentArticleTitle={articleTitle || ""} predictions={sidebarPredictions} />
        <div className="pr-4 sm:pr-6 lg:pr-8 py-12 flex-1">
          <div className="w-full">
            <h1 id={articleTitle || ""} className="text-2xl font-bold text-gray-800 mb-4">
              {articleTitle}
            </h1>
            <div className="flex justify-start mb-2">
              <button
                onClick={handleBackButtonClick}
                className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
              >
                <span className="text-blue-700">Close article</span>
              </button>
              <button
                onClick={handleToggleCollapse}
                className="ml-4 text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
              >
                <span className="text-blue-700">
                  {isCollapsed ? "Expand" : "Collapse"} article
                </span>
              </button>
            </div>
            {!isCollapsed && (
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{ __html: articleContents || "" }}
              />
            )}
          </div>
        </div>
      </div>
      <hr className="my-4 border-t-4 border-gray-300" />
      <div className="w-full">
        <ChatCopy currentArticle={Array.isArray(urlID) ? urlID[0] : urlID} />
      </div>
    </div>
  );
}