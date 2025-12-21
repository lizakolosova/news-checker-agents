import {TIER_CONFIG} from "../config/constants.ts";

const SourceBadge = ({ tier }) => {
  const config = TIER_CONFIG[tier] || TIER_CONFIG.Unknown;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${config.color}`}
      role="status"
      aria-label={`Source tier: ${tier}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{tier}</span>
    </span>
  );
};

export default SourceBadge;