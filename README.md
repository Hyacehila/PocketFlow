<div align="center">
  <img src="https://github.com/The-Pocket/.github/raw/main/assets/title.png" alt="Pocket Flow – 100-line minimalist LLM framework" width="600"/>
</div>

<!-- For translation, replace English with [English](https://github.com/The-Pocket/PocketFlow/blob/main/README.md), and remove the link for the target language. -->

English | [中文](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md) | [Español](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_SPANISH.md) | [日本語](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_JAPANESE.md) | [Deutsch](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md) | [Русский](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_RUSSIAN.md) | [Português](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_PORTUGUESE.md) | [Français](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_FRENCH.md) | [한국어](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-batch/translations/README_KOREAN.md)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](https://the-pocket.github.io/PocketFlow/)
 <a href="https://discord.gg/hUHHE9Sa6T">
    <img src="https://img.shields.io/discord/1346833819172601907?logo=discord&style=flat">
</a>

Pocket Flow is a [100-line](https://github.com/The-Pocket/PocketFlow/blob/main/pocketflow/__init__.py) minimalist LLM framework.And this is an enhenced version.  

- **Lightweight**: Just 100 lines. Zero bloat, zero dependencies, zero vendor lock-in.
  
- **Expressive**: Everything you love—([Multi-](https://the-pocket.github.io/PocketFlow/design_pattern/multi_agent.html))[Agents](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html), [Workflow](https://the-pocket.github.io/PocketFlow/design_pattern/workflow.html), [RAG](https://the-pocket.github.io/PocketFlow/design_pattern/rag.html), and more.

- **[Agentic Coding](https://zacharyhuang.substack.com/p/agentic-coding-the-most-fun-way-to)**: Let AI Agents (e.g., Cursor AI) build Agents—10x productivity boost!

To adhere to the commitment of keeping the codebase within 100 lines, Pocketflow retains only the essential structural framework without offering any wrapped functional implementations. Nevertheless, a moderate level of encapsulation can be beneficial for more efficient development, provided that developers understand what they are encapsulating and their intended use. This is an individual’s enhanced version of the Pocketflow-PythonSDK, incorporating elements that I deem useful but could potentially increase the line count, such as wrappers for RAG (potentially referring to a specific technology or framework). This project is a direct fork of the original SDK, with only minimal alterations to the README file to describe the additional features I’ve implemented and the removal of superfluous content.


## How does Pocket Flow work?

The [100 lines](https://github.com/The-Pocket/PocketFlow/blob/main/pocketflow/__init__.py) capture the core abstraction of LLM frameworks: Graph!
<br>
<div align="center">
  <img src="https://github.com/The-Pocket/.github/raw/main/assets/abstraction.png" width="900"/>
</div>
<br>

From there, it's easy to implement popular design patterns like ([Multi-](https://the-pocket.github.io/PocketFlow/design_pattern/multi_agent.html))[Agents](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html), [Workflow](https://the-pocket.github.io/PocketFlow/design_pattern/workflow.html), [RAG](https://the-pocket.github.io/PocketFlow/design_pattern/rag.html), etc.
<br>
<div align="center">
  <img src="https://github.com/The-Pocket/.github/raw/main/assets/design.png" width="900"/>
</div>
<br>




## How to Use Pocket Flow?

🚀 Through **Agentic Coding**—the fastest LLM App development paradigm-where *humans design* and *agents code*!

<br>
<div align="center">
  <a href="https://zacharyhuang.substack.com/p/agentic-coding-the-most-fun-way-to" target="_blank">
    <img src="https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F423a39af-49e8-483b-bc5a-88cc764350c6_1050x588.png" width="700" alt="IMAGE ALT TEXT" style="cursor: pointer;">
  </a>
</div>
<br>

✨ Below are examples of more complex LLM Apps:

<div align="center">
  
|  App Name     |  Difficulty    | Topics  | Human Design | Agent Code |
| :-------------:  | :-------------: | :---------------------: |  :---: |  :---: |
| [Website Chatbot](https://github.com/The-Pocket/PocketFlow-Tutorial-Website-Chatbot) <br> <sup><sub>Turn your website into a 24/7 customer support genius</sup></sub> | ★★☆ <br> *Medium* | [Agent](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html) <br> [RAG](https://the-pocket.github.io/PocketFlow/design_pattern/rag.html) | [Design Doc](https://github.com/The-Pocket/PocketFlow-Tutorial-Website-Chatbot/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/PocketFlow-Tutorial-Website-Chatbot/blob/main/flow.py)
| [Danganronpa Simulator](https://github.com/The-Pocket/PocketFlow-Tutorial-Danganronpa-Simulator) <br> <sup><sub>Forget the Turing test. Danganronpa, the ultimate AI experiment!</sup></sub> | ★★★ <br> *Advanced*   | [Workflow](https://the-pocket.github.io/PocketFlow/design_pattern/workflow.html) <br> [Agent](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html) | [Design Doc](https://github.com/The-Pocket/PocketFlow-Tutorial-Danganronpa-Simulator/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/PocketFlow-Tutorial-Danganronpa-Simulator/blob/main/flow.py)
| [Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge) <br> <sup><sub>Life's too short to stare at others' code in confusion</sup></sub> |  ★★☆ <br> *Medium* | [Workflow](https://the-pocket.github.io/PocketFlow/design_pattern/workflow.html) | [Design Doc](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge/blob/main/flow.py)
| [Build Cursor with Cursor](https://github.com/The-Pocket/Tutorial-Cursor) <br> <sup><sub>We'll reach the singularity soon ...</sup></sub> | ★★★ <br> *Advanced*   | [Agent](https://the-pocket.github.io/PocketFlow/design_pattern/agent.html) | [Design Doc](https://github.com/The-Pocket/Tutorial-Cursor/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/Tutorial-Cursor/blob/main/flow.py)
| [Ask AI Paul Graham](https://github.com/The-Pocket/Tutorial-YC-Partner) <br> <sup><sub>Ask AI Paul Graham, in case you don't get in</sup></sub> | ★★☆ <br> *Medium*  | [RAG](https://the-pocket.github.io/PocketFlow/design_pattern/rag.html) <br> [Map Reduce](https://the-pocket.github.io/PocketFlow/design_pattern/mapreduce.html) <br> [TTS](https://the-pocket.github.io/PocketFlow/utility_function/text_to_speech.html) | [Design Doc](https://github.com/The-Pocket/Tutorial-AI-Paul-Graham/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/Tutorial-AI-Paul-Graham/blob/main/flow.py)
| [Youtube Summarizer](https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple)  <br> <sup><sub> Explain YouTube Videos to you like you're 5 </sup></sub> | ★☆☆ <br> *Beginner*   | [Map Reduce](https://the-pocket.github.io/PocketFlow/design_pattern/mapreduce.html) |  [Design Doc](https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple/blob/main/docs/design.md) | [Flow Code](https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple/blob/main/flow.py)
| [Cold Opener Generator](https://github.com/The-Pocket/Tutorial-Cold-Email-Personalization)  <br> <sup><sub> Instant icebreakers that turn cold leads hot </sup></sub> | ★☆☆ <br> *Beginner*   | [Map Reduce](https://the-pocket.github.io/PocketFlow/design_pattern/mapreduce.html) <br> [Web Search](https://the-pocket.github.io/PocketFlow/utility_function/websearch.html) |  [Design Doc](https://github.com/The-Pocket/Tutorial-Cold-Email-Personalization/blob/master/docs/design.md) | [Flow Code](https://github.com/The-Pocket/Tutorial-Cold-Email-Personalization/blob/master/flow.py)


</div>

## What Changed

Nothing Changed for now. I am doing on RAG,Visualization,Code Unit Testing.

