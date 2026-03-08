# [Delete your CLAUDE.md (and your AGENT.md too)](https://www.youtube.com/watch?v=GcNu6wrLTJc)

# Delete Your CLAUDE.md (and Your AGENT.md Too)

## The Study Results

Are you really an AI engineer if you haven't put a ton of time into your Agent MD or Claude MD files? Everyone's doing it. It has to be good, right? Well, what if a study just came out showing that those Claude MD and Agent MD files actually made performance worse?

When given an Agent MD or Claude MD file, models consistently performed worse across Sonnet 4.5, GPT-4o, GPT-4o mini, and Claude 3. This is something we should be talking about.

I've been told so many times that I'm having prompt issues because I didn't write an Agent MD or Claude MD. They're supposedly so important. Every codebase needs them. Everybody's publishing their own rule files and skills and all these things. It would be pretty bad if it turned out those things were making the tools worse, right?

On one hand, a lot of people are using these files wrong. On the other hand, it's likely that they shouldn't be used at all for many cases because they steer models incorrectly. This is a deep dive on context management and best practices for using AI to code and build real software.

## What Studies Are Showing

It's been awesome to see studies like this recently popping up:

- Figuring out if these Agent MD files are actually useful
- Skills Bench: figuring out how useful skills are
- Benchmarks trying to figure out why models are more likely to get a question right if you ask them the same thing twice

There's a lot of fun stuff to dive into here, and it's all about context management. This can help you get better at using AI to code.

## How Context Works

To understand Agent MD and Claude MD files, we need to understand how context management works.

When you make a prompt to an AI system, that prompt is not the only thing the model is getting. The user asks a question and the model gives an answer. If you have a follow-up question, you add that and it gets added to the context. When you ask a question, that gets put in the context, and the model autocompletes from there based on all the information it has—all of the text that exists above it. The model is predicting what the most likely next set of characters is, and it does that over and over again until it has an answer.

### The Context Hierarchy

Your question is not actually the thing at the start of the context. Before that, we have other layers. The hierarchy goes:

1. **Provider instructions** — The top level. Things OpenAI or Anthropic have baked in that nothing can override.
2. **System prompt** — Describes what the agent's role is. Takes precedence over user prompts.
3. **Developer message / Developer prompt** — A new layer between the system prompt and the user prompt. This is where Agent MD, Claude MD, and custom Cursor rules exist.
4. **User message** — Your actual prompt.

When you send a message, you're not just sending that one message. You're sending the message and everything above it. When you send a request to Claude's API, you're sending up your chat history, and the system appends the system prompt and the other data on top, then sends that off to the model.

## The Problem With Context Files

When you add information to this developer message layer, you're adding to the context that every single token must traverse. This is expensive and distracting.

Think about it like this: We all hate having endless meetings as developers where we don't need to know all the intricate details of the five versions that product and design went back and forth on before we implement something. Why do we think the AI likes it more than us? Why are we giving them all of this useless information?

The way these files work is simple context management. If you tell the agent about all of these things that exist in your codebase, it's probably going to think about those even if you don't want it to.

### The TRPC Example

For example, in the T3 project's Agent MD, mentioning that they use TRPC on the backend is now going to bias the model towards using TRPC even though they only use it for a handful of legacy functions. Almost everything is now on Convex. Not only does the agent know we have TRPC, we actually put it in front of the Convex part. So it is much more likely to reach for TRPC where it might not make sense.

This is related to something important: **Don't think about pink elephants. You're all now thinking about pink elephants.** That's how brains work and that's how LLMs work too. If you tell it not to do a thing, it's now thinking about that thing.

## The Research Findings

The study benchmarked context files and their impact on resolving GitHub issues. They tested three conditions:

1. Developer-provided instruction files
2. No context file
3. LLM-generated context files

The results:

- Developer-provided files only marginally improved performance compared to omitting them entirely: a 4% increase on average
- LLM-generated context files had a small negative effect: a 3% decrease on average
- These observations are robust across different LLMs and prompts
- Context files led to increased exploration, testing, and reasoning, resulting in increased costs by over 20%

The recommendation: Emit LLM-generated context files for the time being, contrary to agent developer recommendations. Include only minimal requirements like specific tooling to use with the repository.

## Real-World Testing

I ran an init on a real project I've been working on called Lawn, an alternative to frame.io for video review. When I asked it the same question with and without the generated Claude MD file:

- **Without Claude MD:** 1 minute 11 seconds
- **With Claude MD:** 1 minute 29 seconds

The agent MD added a 25% penalty in time. And just like all other docs, agent MD files will go out of date. If the codebase changes and somebody forgets to update the MD file, not only is it not helping, it's actively hurting.

As someone pointed out in the chat: "I had issues with project structures being outdated in the Agent MD file. The models were consistently placing files in the wrong location." This happens all the time. Outdated context files are going to cause you way more problems.

## What Actually Matters

If the information is in the codebase, it probably doesn't need to be in the Agent MD file. These models have been trained to do bash calls and use the tools provided to them. They're good at finding information in a codebase.

These models are really good at:
- Figuring out what files and folders matter for their task
- Figuring out what commands they can run by checking your package.json
- Figuring out what dependencies you have

The best time to update your Agent MD isn't when you start a project. It's when you notice the model consistently doing something wrong and you want to steer it in a different direction.

## My Philosophy on Agent MD Files

I use these files to steer the model away from things it's consistently doing wrong. I'm surprised at how rare that is nowadays. With every new model release, I can delete more and more of the Agent MD. I'll sometimes just delete it entirely when trying a new model and see what changes, then bring back the parts that matter.

Here's my template for what should actually go in these files:

The role of this file is to describe common mistakes and confusion points that agents might encounter as they work in this project. If you ever encounter something in the project that surprises you, please alert the developer working with you and indicate that this is the case in the AGENTS.md file to help prevent future agents from having the same issue.

That's it. If you ever encounter something in the project that surprises you, that's what belongs here—not general information about the codebase.

### My Personal Hack

I'll put instructions for agents to alert me about confusion points. Not because I want them constantly changing the Claude MD or Agent MD files, but because when the agent gets stuck on something or thinks something is surprising or confusing, that's usually not something I want it to know about. It's something I want to go fix in the codebase itself.

I merge less than a fifth of the changes the agent proposes to the Agent MD. The other four out of five I use to make the codebase better.

## Better Approaches Than Agent MD Files

Rather than updating your Agent MD or Claude MD file, spend your time on:

1. **Better code organization** — If models are struggling to find something, it's probably in a bad place. Move it.
2. **Better tooling** — If agents are struggling to use a tool properly, it might not be the right tool for the job or might be shaped in a way that's confusing. Fix it.
3. **Better feedback systems** — Make sure agents have the tools they need to unblock themselves.
4. **Better tests** — Unit tests, integration tests, type checks, and those types of things that you can expose to the model.

If you can make it easier for the model to do the right thing, make it harder for it to do the wrong thing, and have your whole codebase architected to steer it in the right direction, that's going to be a much bigger win. The Agent MD is almost like a band-aid solution. You're patching over a problem with it.

## Advanced Techniques

Developers don't understand how powerful it is to lie or intentionally mislead the agents in ways that set both you and the agent up for more success.

Examples:

- Tell the agent "Hey, this app has no users. There's no real data yet. Make whatever changes you want and don't worry about it" even if the project's already live, because you don't want it spending a ton of time on weird backfill data patterns.
- Put in the Claude MD: "This project is super green field. It's okay if you change the schema entirely. We're trying to get it in the right shape."
- If you're trying to build something that takes multiple steps and you're asking it to do step two over and over and it keeps failing, ask it for step three. It will try step two to get there, it won't work, and it will often fix itself.

These are clever engineering hacks. You build an intuition for how models behave and what context matters through time in the saddle.

## The Bigger Picture

If you're filling the context with giant Claude MD files, piles of skills you downloaded from the internet, a bunch of MCP servers you're not using, and a bunch of Cursor rules somebody told you about on GitHub, you'll never be able to diagnose why the model's doing things wrong.

If all you have is your codebase, your prompt, and a minimal Agent MD file, you've meaningfully reduced the places where the agent can be misled. Everything the agents do exists because of one of the sources it has. If you can reduce those sources, you can make it much more likely that it behaves correctly.

## Final Thoughts

You need to experiment a bunch. This is so different from how coding used to look. Certain skills end up more important than ever, and others are just new things you're going to have to build as you go.

The core philosophy: Use these files to steer the model away from things that are consistently doing wrong. That's it. Delete the rest.