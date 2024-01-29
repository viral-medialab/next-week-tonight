import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

interface ArticleProps {
  articleTitle: string;
  articleContent: string;
  articleImage?: string;
  articleUrl: string; // Add the article URL
  onClose: () => void;
}

interface ArticleInfo {
  title: string;
  author: string;
  contents: string;
}

interface SidebarProps {
  history: { title: string; url: string }[];
  setHistory: React.Dispatch<React.SetStateAction<{ title: string; url: string }[]>>;
}

const Sidebar: React.FC<SidebarProps> = ({ history, setHistory }) => {
  const currentArticle = history.length > 0 ? history[0] : null;

  return (
    <div className="w-1/5 bg-gray-200 p-4 m-4 h-full">
      <h2 className="text-lg font-semibold mb-4">History</h2>
      <ul>
        {currentArticle && (
          <li className="mb-2">
            <a href={currentArticle.url} target="_self" rel="noopener noreferrer">
              {currentArticle.title}
            </a>
          </li>
        )}
      </ul>
      <li className="mb-2">Prediction 1</li>
      <li className="mb-2">Prediction 2</li>
      <li className="mb-2">Prediction 3</li>
    </div>
  );
};

export default function Article({
  articleTitle,
  articleContent,
  articleImage,
  articleUrl,
  onClose,
}: ArticleProps) {
  const [visitedArticles, setVisitedArticles] = useState<{ title: string; url: string }[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [articleInfo, setArticleInfo] = useState<ArticleInfo | null>(null);

  // Load history from localStorage on component mount
  useEffect(() => {
    const storedHistory = localStorage.getItem("visitedArticlesHistory");
    if (storedHistory) {
      setVisitedArticles(JSON.parse(storedHistory));
    }
  }, []);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("visitedArticlesHistory", JSON.stringify(visitedArticles));
  }, [visitedArticles]);

  useEffect(() => {
    const currentUrl = window.location.href;
    setVisitedArticles((prevVisitedArticles) => [
      { title: articleTitle, url: articleUrl || currentUrl },
      ...prevVisitedArticles,
    ]);

    // Fetch article information
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

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: ArticleInfo = await response.json();
        setArticleInfo(data);
        console.log(data);
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
      <Sidebar history={visitedArticles} setHistory={setVisitedArticles} />
      <div className="pr-4 sm:pr-6 lg:pr-8 py-12 flex-1">
        <div className="w-full">
          <h1 id={articleTitle} className="text-2xl font-bold text-gray-800 mb-4">
            <a href={articleUrl || window.location.href} target="_self" rel="noopener noreferrer">
              {articleInfo?.title || articleTitle}
            </a>
          </h1>
          {articleImage && (
            <img
              src={articleImage}
              alt={articleInfo?.title || articleTitle}
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
              dangerouslySetInnerHTML={{ __html: articleInfo?.contents}}
            />
          )}
        </div>
      </div>
    </div>
  );
}