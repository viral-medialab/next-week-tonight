import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

interface ArticleProps {
  articleTitle: string;
  articleContent: string;
  articleImage?: string;
  onClose: () => void;
}

interface SidebarProps {
  history: { title: string; url: string }[];
  setHistory: React.Dispatch<React.SetStateAction<{ title: string; url: string }[]>>;
}

const Sidebar: React.FC<SidebarProps> = ({ history, setHistory }) => (
  <div className="w-1/5 bg-gray-200 p-4 m-4 h-full">
    <h2 className="text-lg font-semibold mb-4">History</h2>
    <ul>
      {history.map(({ title, url }, index) => (
        <li key={index} className="mb-2">
          <a href={url} target="_self" rel="noopener noreferrer">
            {title}
          </a>
        </li>
      ))}
    </ul>
  </div>
);

export default function Article({
  articleTitle,
  articleContent,
  articleImage,
  onClose,
}: ArticleProps) {
  const [visitedArticles, setVisitedArticles] = useState<{ title: string; url: string }[]>([]);

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
    const currentPath = window.location.pathname;
    const isAlreadyVisited = visitedArticles.some((entry) => entry.title === articleTitle);

    if (!isAlreadyVisited) {
      const newUrl = `${currentPath}/${articleTitle}`;

      // Change the URL using history.pushState
      window.history.pushState({}, articleTitle, newUrl);

      setVisitedArticles((prevVisitedArticles) => [
          { title: articleTitle, url: newUrl },
          ...prevVisitedArticles.slice(0, 9), // Keep up to 10 existing entries
        ]);
    }
  }, [articleTitle]);

  return (
    <div className="flex">
      <Sidebar history={visitedArticles} setHistory={setVisitedArticles} />
      <div className="pr-4 sm:pr-6 lg:pr-8 py-12 flex-1">
        <div className="w-full">
          <h1 id={articleTitle} className="text-2xl font-bold text-gray-800 mb-4">
            <a href={window.location.href} target="_self" rel="noopener noreferrer">
              {articleTitle}
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
          </div>
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: articleContent }}
          />
        </div>
      </div>
    </div>
  );
}