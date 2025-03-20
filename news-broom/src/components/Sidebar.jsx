
import { useState } from "react";
import { FaPlus, FaFileAlt, FaBars } from "react-icons/fa";
import { IoNewspaperOutline } from "react-icons/io5";
import { MdOutlineBubbleChart } from "react-icons/md";
import { Link } from "react-router-dom";
import { NavLink } from "react-router-dom";
import Logofooter from "../assets/images/bottomLogo.png";
const Sidebar = () => {
  const [active, setActive] = useState("New Report");

  const menuItems = [
    { name: "New Report", path: "/new-project", icon: <FaPlus /> },
    { name: "Canada Sanctions", path: "/", icon: <FaFileAlt /> },
    { name: "Gaza Ceasefire", path: "/", icon: <FaFileAlt /> },
    { name: "Singapore Budget 2025", path: "/", icon: <FaFileAlt /> },
  ];

  return (
    <div className="w-72 h-screen bg-white p-4 flex flex-col border-r shadow-md">
      {/* Top Section: Hamburger + Logo */}
      <div className="flex items-center gap-3 mb-6">
        <FaBars className="text-xl text-black cursor-pointer" />
        <div className="flex items-center gap-2 text-lg font-semibold">
          <IoNewspaperOutline className="text-2xl text-black" />
          <span className="text-black">News Broom</span>
        </div>
      </div>

      {/* Middle Section: Menu Items */}
      <ul className="flex-1 space-y-2">
        {menuItems.map((item) => (
          <li key={item.name}>
            <Link
              to={item.path}
              className={`flex items-center gap-3 p-3 text-sm font-medium rounded-lg cursor-pointer transition-all ${
                active === item.name ? "bg-gray-200 font-semibold" : "hover:bg-gray-100"
              }`}
              onClick={() => setActive(item.name)}
            >
              {item.icon}
              <span className="text-black">{item.name}</span>
            </Link>
          </li>
        ))}
      </ul>

      {/* Bottom Section */}
      <div className="mb-6">
      <NavLink to="/knowledge-graph" className={({ isActive }) => 
          `flex items-center gap-2 p-3 rounded-lg ${isActive ? "bg-black text-white" : "hover:bg-gray-100"}`
        }>
          <MdOutlineBubbleChart />
          Latest Knowledge Graph
        </NavLink>
        <NavLink
  to="/finalvedio"
  className="w-full flex items-center gap-3 p-3 bg-purple-500 text-white text-sm font-medium hover:bg-purple-600 rounded-lg transition"
>
  <MdOutlineBubbleChart className="text-lg" /> Generate News Story
</NavLink>
      </div>

      {/* Footer */}
      <div className="mt-auto text-xs text-gray-600">
        <img src={Logofooter} />
        {/* <p className="text-red-500 font-bold">NEXT</p>
        <p className="text-gray-700 font-semibold">LAST</p>
        <p className="text-black font-extrabold">WEEK TONIGHT</p>
        <p className="text-gray-500 italic">with JANE DOE</p> */}
      </div>
    </div>
  );
};

export default Sidebar;