import { useEffect, useState } from "react";
import { Dialog } from "radix-ui";
import NodeDetails from "./NodeDetails";
import { t } from "../../i18n/t";
export function Drawer({ id, onClose }: { id: string; onClose: () => void }) {
  const [mobile, setMobile] = useState(
    () => matchMedia("(max-width: 767px)").matches,
  );
  useEffect(() => {
    const media = matchMedia("(max-width: 767px)"),
      update = () => setMobile(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, [onClose]);
  if (mobile)
    return (
      <Dialog.Root
        open
        onOpenChange={(open) => {
          if (!open) onClose();
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="drawer-overlay" />
          <Dialog.Content
            className="mobile-drawer"
            aria-describedby={undefined}
          >
            <Dialog.Title className="sr-only">{t("node.details")}</Dialog.Title>
            <Dialog.Close className="drawer-close" aria-label={t("node.close")}>
              ×
            </Dialog.Close>
            <NodeDetails id={id} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    );
  return (
    <aside className="desktop-drawer" aria-label={t("node.details")}>
      <button
        className="drawer-close"
        aria-label={t("node.close")}
        onClick={onClose}
      >
        ×
      </button>
      <NodeDetails id={id} />
    </aside>
  );
}
