import { pageMetadata } from "@/lib/metadata";
export const metadata = pageMetadata("en", "home");
import { Site } from "@/components/site";
export default function Page() {
  return <Site locale="en" section="home" />;
}
