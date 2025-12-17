import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Physical AI & Humanoid Robotics Textbook',
  tagline: 'Building the Future of Embodied Intelligence',
  favicon: 'img/favicon.ico',

  // Production URL
  url: 'https://physical-ai-humanoid-robotics-book-ebon.vercel.app',
  baseUrl: '/',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/Umer-Ali7/Physical-AI-Humanoid-Robotics-Book/edit/main/',
        },
        blog: false, // Blog disabled to remove unnecessary pages
        theme: {
          customCss: './src/css/custom.css',
        },
        // Sitemap configuration yaha daal do (preset ke andar)
        sitemap: {
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/login', '/markdown-page', '/blog/**'],
        },
      } satisfies Preset.Options,
    ],
  ],

  // Plugins array se sitemap hata diya (kyuki preset mein already hai)
  // Agar future mein koi aur plugin add karna ho to yaha daal sakte ho

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    navbar: {
      title: 'Physical AI Textbook',
      logo: {
        alt: 'Physical AI Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'dropdown',
          label: 'Modules',
          position: 'left',
          items: [
            { label: 'Introduction', to: '/docs/intro' },
            { label: 'Module 1: The Robotic Nervous System', to: '/docs/module-01-ros2/architecture' },
            { label: 'Module 2: The Digital Twin', to: '/docs/module-02-digital-twin/gazebo-setup' },
            { label: 'Module 3: The AI-Robot Brain', to: '/docs/module-03-robot-brain/isaac-sim' },
            { label: 'Module 4: Vision-Language-Action', to: '/docs/module-04-vla/voice-control' },
            { label: 'Module 5: Capstone Project', to: '/docs/module-05-capstone/final-project' },
          ],
        },
        {
          href: 'https://github.com/Umer-Ali7/Physical-AI-Humanoid-Robotics-Book',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Curriculum',
          items: [
            { label: 'Introduction', to: '/docs/intro' },
            { label: 'Module 1: The Robotic Nervous System', to: '/docs/module-01-ros2/architecture' },
            { label: 'Module 2: The Digital Twin', to: '/docs/module-02-digital-twin/gazebo-setup' },
            { label: 'Module 3: The AI-Robot Brain', to: '/docs/module-03-robot-brain/isaac-sim' },
            { label: 'Module 4: Vision-Language-Action', to: '/docs/module-04-vla/voice-control' },
            { label: 'Module 5: Capstone Project', to: '/docs/module-05-capstone/final-project' },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'GitHub Repository',
              href: 'https://github.com/Umer-Ali7/Physical-AI-Humanoid-Robotics-Book',
            },
            {
              label: 'Panaversity',
              href: 'https://panaversity.org',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics Textbook. Built with Docusaurus.`,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;