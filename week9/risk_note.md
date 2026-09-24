1. Who wrote it: Internal content team developers and third-party nutritional data contractors without formal security review or code provenance signing.
2. What it can reach: Local host process memory, environment variables, adjacent network databases, and all raw customer recipe prompts routed via tool arguments.
3. What it logs: Query parameters, requested ingredient strings, timestamped call volumes, and diagnostic stack traces written to local stderr.
4. What a stolen token could do: Exfiltrate proprietary recipe formulations, poison allergen metadata (causing life-threatening anaphylactic shock), or pivot internally across VPC resources.
5. Ship or don't: DO NOT SHIP until wrapped in a sandboxed, read-only container with blocked outbound egress, strict token scoping, and automated allergen assertion checks.
