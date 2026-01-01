/**
 * AAL UI Kit - Avatar Component
 * User avatar with fallback initials
 */

import React from "react";

export interface AalAvatarProps {
  /**
   * Image source URL
   */
  src?: string;

  /**
   * Alt text for image
   */
  alt?: string;

  /**
   * Fallback name (used for initials)
   */
  name?: string;

  /**
   * Size in pixels
   * @default 40
   */
  size?: number;

  /**
   * Tone variant
   * @default "cyan"
   */
  tone?: "cyan" | "yellow" | "magenta";

  /**
   * Additional CSS class
   */
  className?: string;

  /**
   * Inline styles
   */
  style?: React.CSSProperties;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function hashColor(str: string): "cyan" | "yellow" | "magenta" {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const colors: ("cyan" | "yellow" | "magenta")[] = ["cyan", "yellow", "magenta"];
  return colors[Math.abs(hash) % colors.length];
}

export function AalAvatar({
  src,
  alt,
  name,
  size = 40,
  tone,
  className = "",
  style,
}: AalAvatarProps) {
  const [imgError, setImgError] = React.useState(false);
  const showImage = src && !imgError;
  const initials = name ? getInitials(name) : "?";
  const autoTone = tone || (name ? hashColor(name) : "cyan");

  return (
    <div
      className={`aal-avatar aal-avatar--${autoTone} ${className}`.trim()}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.4,
        ...style,
      }}
      role="img"
      aria-label={alt || name || "Avatar"}
    >
      {showImage ? (
        <img
          src={src}
          alt={alt || name || "Avatar"}
          className="aal-avatar__image"
          onError={() => setImgError(true)}
        />
      ) : (
        <span className="aal-avatar__initials">{initials}</span>
      )}
    </div>
  );
}

// Avatar group for stacking multiple avatars
export interface AalAvatarGroupProps {
  children: React.ReactNode;
  max?: number;
  size?: number;
  className?: string;
}

export function AalAvatarGroup({
  children,
  max = 4,
  size = 40,
  className = "",
}: AalAvatarGroupProps) {
  const avatars = React.Children.toArray(children);
  const visible = avatars.slice(0, max);
  const overflow = avatars.length - max;

  return (
    <div className={`aal-avatar-group ${className}`.trim()}>
      {visible.map((child, i) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<AalAvatarProps>, {
              size,
              style: { marginLeft: i > 0 ? -size * 0.3 : 0 },
            })
          : child
      )}
      {overflow > 0 && (
        <div
          className="aal-avatar aal-avatar--overflow"
          style={{
            width: size,
            height: size,
            fontSize: size * 0.35,
            marginLeft: -size * 0.3,
          }}
        >
          +{overflow}
        </div>
      )}
    </div>
  );
}
