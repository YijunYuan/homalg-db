import { lazy } from "react";
import { createHashRouter } from "react-router";
import Layout from "./Layout";
import NotFound from "./NotFound";
const Home = lazy(() => import("../features/documents/Home"));
const Document = lazy(() => import("../features/documents/Document"));
const Node = lazy(() => import("../features/node/NodePage"));
const Search = lazy(() => import("../features/search/Search"));
const Tags = lazy(() => import("../features/taxonomy/Tags"));
const Concepts = lazy(() => import("../features/taxonomy/Concepts"));
const Timeline = lazy(() => import("../features/timeline/Timeline"));
const Claims = lazy(() => import("../features/claims/Claims"));
const About = lazy(() => import("../features/documents/About"));
export const router = createHashRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/doc/:docKey", element: <Document /> },
      { path: "/doc/:docKey/node/:localId", element: <Document /> },
      { path: "/doc/:docKey/fidelity", element: <Document /> },
      { path: "/node/:docKey/:localId", element: <Node /> },
      { path: "/search", element: <Search /> },
      { path: "/tags/:id?", element: <Tags /> },
      { path: "/concepts/:id?", element: <Concepts /> },
      { path: "/timeline", element: <Timeline /> },
      { path: "/claims", element: <Claims /> },
      { path: "/about", element: <About /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);
