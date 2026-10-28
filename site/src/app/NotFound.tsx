import { Link } from "react-router";
import { t } from "../i18n/t";
export default function NotFound() {
  return (
    <div className="page">
      <h1>{t("app.notFound")}</h1>
      <Link to="/">{t("app.back")}</Link>
    </div>
  );
}
