import { pageMetadata } from "@/lib/metadata";
export const metadata = pageMetadata("nl", "home");
import { Site } from "@/components/site";
export default function Page() {
  return <Site locale="nl" section="home" />;
}
