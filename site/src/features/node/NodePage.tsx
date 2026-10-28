import { useParams } from "react-router";
import NodeDetails from "./NodeDetails";
export default function NodePage() {
  const { docKey, localId } = useParams();
  return (
    <div className="page standalone-node">
      <NodeDetails id={`${docKey}.${localId}`} />
    </div>
  );
}
