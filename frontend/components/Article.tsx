import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

interface ArticleProps {
  articleTitle: string;
  articleImage?: string;
  articleUrl: string;
  articlePublisher: string;
  articleCategory: string;
  articleID: string;
  onClose: () => void;
}

const Sidebar: React.FC<{ currentArticleTitle: string }> = ({ currentArticleTitle }) => (
  <div className="w-1/5 bg-gray-200 p-4 m-4 h-full">
    <h2 className="text-lg font-semibold mb-4">Navigation</h2>
    <ul>
      <li className="mb-2">
        <a href="#" target="_self" rel="noopener noreferrer">
          {currentArticleTitle}Title Placeholder
        </a>
      </li>
    </ul>
    <p> ↳ Prediction 1</p>
    <p> ↳ Prediction 2</p>
    <p> ↳ Prediction 3</p>
  </div>
);

export default function Article({
  articleTitle,
  articleImage,
  articleUrl,
  articlePublisher,
  articleCategory,
  articleID,
  onClose,
}: ArticleProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [articleContents, setArticleContents] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticleInfo = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/api/gather_article_info", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            articleUrl: articleUrl,
          }),
        });

        console.log("test here");
        console.log(articleUrl)
        console.log(response)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setArticleContents(data["contents"]);
      } catch (error) {
        console.error("Error fetching article info:", error);
      }
    };

    fetchArticleInfo();
  }, [articleTitle, articleUrl]);

  const handleToggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="flex">
      <Sidebar currentArticleTitle={articleTitle} />
      <div className="pr-4 sm:pr-6 lg:pr-8 py-12 flex-1">
        <div className="w-full">
          <h1 id={articleTitle} className="text-2xl font-bold text-gray-800 mb-4">
            <a href={articleUrl || window.location.href} target="_self" rel="noopener noreferrer">
              {articleTitle}Title Placeholder
            </a>
          </h1>
          {articleImage && (
            <img
              src={articleImage}
              alt={articleTitle}
              className="rounded-lg shadow-lg mb-8 w-3/4"
            />
          )}
          <div className="flex justify-start mb-2">
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
            >
              <span className="text-blue-700">Close article</span>
            </button>
            <button
              onClick={handleToggleCollapse}
              className="ml-4 text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
            >
              <span className="text-blue-700">{isCollapsed ? 'Expand' : 'Collapse'} article</span>
            </button>
          </div>
          {!isCollapsed && (
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: articleContents }}
            />
          )}
        </div>
      </div>
    </div>
  );
}