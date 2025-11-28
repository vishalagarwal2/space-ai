/**
 * Mock Business Profiles for Testing
 * These profiles contain complete business information including color palettes
 */

export interface DesignComponents {
  instructions: string;
  componentRules: {
    headerText: {
      description: string;
      styling: {
        textTransform?: "uppercase" | "lowercase" | "capitalize" | "none";
        color?: string; // Can reference brand colors like 'primary' or specific hex
        fontWeight?: string;
        additionalStyles?: string;
      };
      usage: string;
    };
    bodyText: {
      description: string;
      styling: {
        textTransform?: "uppercase" | "lowercase" | "capitalize" | "none";
        color?: string;
        fontWeight?: string;
        additionalStyles?: string;
      };
      usage: string;
    };
    specialBannerText: {
      description: string;
      styling: {
        textTransform?: "uppercase" | "lowercase" | "capitalize" | "none";
        color?: string;
        fontWeight?: string;
        backgroundColor?: string; // Can reference brand colors
        borderRadius?: number; // Border radius in pixels (0 for no radius)
        additionalStyles?: string;
      };
      usage: string;
    };
  };
}

export interface BusinessProfile {
  id: string;
  name: string;
  companyName: string;
  logoUrl?: string;
  postLogoUrl?: string;
  colorPalette: {
    primary: string;
    secondary: string;
    accent?: string;
    background?: string;
  };
  brandGuidelines: {
    fontFamily: string;
    tagline?: string;
    industry: string;
  };
  designComponents: DesignComponents;
  defaultTemplate?: string;
  website_url?: string;
  instagram_handle?: string;
  brand_mission?: string;
  brand_values?: string;
  business_basic_details?: string;
  business_services?: string;
  business_context?: string;
  business_additional_details?: string;
}

export const MOCK_BUSINESS_PROFILES: BusinessProfile[] = [
  {
    id: "miraai-recycling",
    name: "Miraai Recycling",
    companyName: "Miraai Recycling",
    logoUrl: "/images/miraai-logo.png",
    postLogoUrl: "/images/miraai-logo-full.png",
    colorPalette: {
      primary: "#44B549", // Green for sustainability
      secondary: "#3F3F3F", // Black
      accent: "#34D399", // Light green
      background: "#F0FDF4", // Very light green
    },
    brandGuidelines: {
      fontFamily: "Aleo",
      tagline: "Sustainable Solutions for Tomorrow",
      industry: "Environmental Services",
    },
    designComponents: {
      instructions:
        "Create engaging, sustainability-focused designs with clear visual hierarchy. Use eco-friendly messaging and emphasize the environmental benefits.",
      componentRules: {
        headerText: {
          description:
            "For main slogans/headlines (like 'Scrap. Save. Smile.')",
          styling: {
            textTransform: "none",
            color: "#000", // Will use brand primary color
            fontWeight: "bold",
            additionalStyles: "Gets LARGE font size, maximum visual impact",
          },
          usage: "Use when: Main slogan, primary headline, key catchphrase",
        },
        bodyText: {
          description: "For regular supporting content",
          styling: {
            textTransform: "none",
            color: "#333333",
            fontWeight: "normal",
            additionalStyles: "Gets medium font size, standard styling",
          },
          usage:
            "Use when: Supporting information, descriptions, secondary messages",
        },
        specialBannerText: {
          description:
            "For highlighted offers/CTAs (like 'Upto ₹75,000 Road Tax Rebate')",
          styling: {
            textTransform: "none",
            color: "#FFFFFF",
            fontWeight: "bold",
            backgroundColor: "primary",
            borderRadius: 25, // Rounded corners for eco-friendly look
            additionalStyles:
              "Gets prominent styling with background color banner/pill effect",
          },
          usage:
            "Use when: Special offers, important numbers, call-to-action buttons",
        },
      },
    },
    defaultTemplate: "miraai-modern-image", // Company-specific template
    website_url: "https://miraairecycling.com/",
    instagram_handle: "@miraairecycling",
    business_basic_details:
      "Goa's Trusted Vehicle Recycling Facility. We specialise in responsible end-of-life vehicle processing for all makes and models. Our streamlined service ensures a hassle-free way for you to contribute to a greener future.​",
    brand_mission:
      "To revolutionize waste management by making recycling accessible, efficient, and rewarding for communities and businesses.",
    brand_values:
      "Sustainability, Innovation, Community Impact, Environmental Responsibility, Transparency",
    business_services:
      "Scrap your old vehicle and save upto ₹1,00,000 on your next ride!",
    business_context:
      "Why Recycle? When your vehicle reaches the end of its road, responsible scrap recycling is not only good for the environment but also for your finances! Some benefits that India’s Vehicle Scrapping Policy offers are",
    business_additional_details: `MIRAAI, denoting “”future”” in Japanese, is Goa’s trusted partner for all your
     scrap recycling needs. We offer reliable and efficient scrap collection, competitive prices, and environmentally friendly disposal practices. With MIRAAI, you can clear your clutter, knowing you’re contributing to a greener Goa while receiving top value for your scrap metal.`,
  },
  {
    id: "tailwind-financial",
    name: "Tailwind Financial Services",
    companyName: "Tailwind Financial Services",
    logoUrl: "/images/tailwind-logo.png",
    postLogoUrl: "/images/tailwind-logo.png",
    colorPalette: {
      primary: "#1E40AF", // Professional blue
      secondary: "#10365F", // Dark blue
      accent: "#60A5FA", // Light blue
      background: "#EFF6FF", // Very light blue
    },
    brandGuidelines: {
      fontFamily: "Optika",
      tagline: "Your Financial Future, Secured",
      industry: "Financial Services",
    },
    designComponents: {
      instructions:
        "Create professional, trustworthy financial services designs. All text should be in UPPERCASE for brand consistency. Headers should use the primary brand color to establish authority and trust.",
      componentRules: {
        headerText: {
          description:
            "For main headlines and slogans in financial services style",
          styling: {
            textTransform: "uppercase",
            color: "#10365F", // Will use brand primary color (#1E40AF)
            fontWeight: "bold",
            additionalStyles:
              "Gets LARGE font size, bold, maximum visual impact, professional appearance",
          },
          usage:
            "Use when: Main financial headlines, service announcements, key value propositions",
        },
        bodyText: {
          description: "For supporting financial content and descriptions",
          styling: {
            textTransform: "lowercase",
            color: "#333333",
            fontWeight: "500",
            additionalStyles:
              "Gets medium font size, professional styling, semi-bold",
          },
          usage:
            "Use when: Service descriptions, supporting information, professional details",
        },
        specialBannerText: {
          description:
            "For important financial offers and call-to-actions. Use attention-grabbing headlines that either pose thought-provoking questions (e.g., 'WHY RICH PEOPLE DON'T BUY CARS') or present imperative statements about essential financial concepts (e.g., 'MONEY BOUNDARIES EVERYONE MUST HAVE!'). Keep headlines concise, use all caps or mixed case for emphasis, and focus on actionable insights or surprising perspectives.",
          styling: {
            textTransform: "uppercase",
            color: "#FFFFFF",
            fontWeight: "bold",
            backgroundColor: "primary",
            borderRadius: 0, // No border radius for Tailwind's professional look
            additionalStyles:
              "Gets prominent styling with primary color background banner",
          },
          usage:
            "Use when: Highlighting thought-provoking financial concepts, essential money management principles, wealth psychology insights, or educational content about smart financial decisions. Ideal for content that creates curiosity and encourages users to learn more about strategic financial behavior.",
        },
      },
    },
    defaultTemplate: "general-cross-pattern", // Professional template
    website_url: "https://tailwindfinancial.com/",
    instagram_handle: "@tailwindfinancial",
    brand_mission:
      "To make financial decisions easier while striving to provide the most comprehensive offerings which are completely digital and secure while providing the best customer service",
    brand_values:
      "Trust, Expertise, Client-First Approach, Financial Literacy, Long-term Growth",
    business_basic_details:
      "The Complete Investment Solution for your Financial Needs.",
    business_services:
      "Plan, Save & Invest. All in one Place. We help you invest in mutual funds, venture capital, Corporate FDs and bonds, PMFs / AIFs",
    business_additional_details:
      "Tailwind is built for Everybody. Our uniquely built platform allows you to invest in variety of solutions curated for all your investing needs, and manage your entire family’s investments from one place.",
  },
  {
    id: "tela",
    name: "Tela",
    companyName: "Tela",
    logoUrl: "/images/tela-logo.png",
    postLogoUrl: "/images/tela-logo.png",
    colorPalette: {
      primary: "#8B5CF6", // Purple for creativity
      secondary: "#6D28D9", // Dark purple
      accent: "#A78BFA", // Light purple
      background: "#F5F3FF", // Very light purple
    },
    brandGuidelines: {
      fontFamily: "Poppins",
      tagline: "Weaving Digital Experiences",
      industry: "Technology & Design",
    },
    designComponents: {
      instructions:
        "Create modern, creative designs that showcase innovation and digital expertise. Use contemporary styling with creative flair.",
      componentRules: {
        headerText: {
          description: "For main creative headlines and design-focused slogans",
          styling: {
            textTransform: "none",
            color: "primary", // Will use brand primary color (#8B5CF6)
            fontWeight: "bold",
            additionalStyles:
              "Gets LARGE font size, creative and modern styling",
          },
          usage:
            "Use when: Creative headlines, design announcements, innovation messaging",
        },
        bodyText: {
          description:
            "For supporting creative content and design descriptions",
          styling: {
            textTransform: "none",
            color: "#333333",
            fontWeight: "normal",
            additionalStyles: "Gets medium font size, modern styling",
          },
          usage:
            "Use when: Design descriptions, creative process info, supporting details",
        },
        specialBannerText: {
          description: "For highlighted creative offers and design CTAs",
          styling: {
            textTransform: "none",
            color: "#FFFFFF",
            fontWeight: "bold",
            backgroundColor: "primary",
            borderRadius: 25, // Rounded corners for creative look
            additionalStyles:
              "Gets prominent styling with creative purple background banner",
          },
          usage:
            "Use when: Design offers, creative services, call-to-action buttons, portfolio highlights",
        },
      },
    },
    defaultTemplate: "general-grid-pattern", // Creative template
    website_url: "https://tela.design/",
    instagram_handle: "@teladesign",
    brand_mission:
      "To create stunning, user-centric digital experiences that help brands connect with their audiences in meaningful ways.",
    brand_values:
      "Creativity, User Experience, Innovation, Collaboration, Design Excellence",
  },
];

export const DEFAULT_BUSINESS_PROFILE = MOCK_BUSINESS_PROFILES[0];
