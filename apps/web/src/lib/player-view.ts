import type {
  ProfileIndex as LegacyIndex,
  ProfileIndexEntry as LegacyEntry,
  ProfileScope,
  ProfileDetail as LegacyDetail,
} from "./profile-contracts";
import type { ExpandedDetail, CapabilitySet } from "./expansion-contracts";
export type ProfileIndexEntry = LegacyEntry & {
  capabilities_v12?: CapabilitySet;
  detail_path?: string;
};
export type ProfileIndex = Omit<
  LegacyIndex,
  "version" | "profiles" | "scopes"
> & {
  version: "player-database-v1" | "player-database-v12";
  profiles: ProfileIndexEntry[];
  scopes: Array<
    ProfileScope & {
      country?: string;
      scope_label?: string;
      recruitment?: boolean;
      clubs?: string[];
    }
  >;
};
export type ProfileDetail = LegacyDetail | ExpandedDetail;
