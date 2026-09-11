import { glob } from 'astro/loaders'
import { defineCollection, z } from 'astro:content'

function removeDupsAndLowerCase(array: string[]) {
  if (!array.length) return array
  const lowercaseItems = array.map((str) => str.toLowerCase())
  const distinctItems = new Set(lowercaseItems)
  return Array.from(distinctItems)
}

// Define blog collection
const blog = defineCollection({
  // Load Markdown and MDX files in the `src/content/blog/` directory.
  loader: glob({
    base: './src/content/blog',
    pattern: ['**/*.{md,mdx}', '!AGENTS.md', '!**/.opencode/**']
  }),
  // Required
  schema: ({ image }) =>
    z.object({
      // Required
      title: z.string().max(60),
      description: z.string().max(160),
      publishDate: z.coerce.date(),
      // Optional
      updatedDate: z.coerce.date().optional(),
      heroImage: z
        .object({
          src: image(),
          alt: z.string().optional(),
          inferSize: z.boolean().optional(),
          width: z.number().optional(),
          height: z.number().optional(),

          color: z.string().optional()
        })
        .optional(),
      tags: z.array(z.string()).default([]).transform(removeDupsAndLowerCase),
      language: z.string().optional(),
      draft: z.boolean().default(false),
      // Special fields
      comment: z.boolean().default(true),
      ai: z.enum(['human', 'assisted', 'ai']).default('human')
    })
})

// Define commands collection for atomic cheatsheets
const commands = defineCollection({
  loader: glob({
    base: './src/content/commands',
    pattern: '**/*.{md,mdx}'
  }),
  schema: z.object({
    title: z.string().optional(),
    desc: z.string(),
    tags: z.array(z.string()).default([]).transform(removeDupsAndLowerCase),
    related: z.array(z.string()).default([])
  })
})

export const collections = { blog, commands }
