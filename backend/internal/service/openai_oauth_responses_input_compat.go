package service

import "strings"

// normalizeOpenAIOAuthResponsesInputItems wraps legacy top-level text items into
// message-shaped input for ChatGPT/Codex OAuth upstreams.
func normalizeOpenAIOAuthResponsesInputItems(reqBody map[string]any) bool {
	if reqBody == nil {
		return false
	}
	input, ok := reqBody["input"].([]any)
	if !ok || len(input) == 0 {
		return false
	}

	changed := false
	for i, raw := range input {
		item, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		itemType := strings.TrimSpace(firstNonEmptyString(item["type"]))
		if itemType == "message" || itemType == "reasoning" || itemType == "function_call" || itemType == "function_call_output" || itemType == "item_reference" {
			continue
		}

		role := "user"
		contentType := "input_text"
		switch itemType {
		case "output_text":
			role = "assistant"
			contentType = "output_text"
		case "input_text", "text":
			// Keep default user/input_text mapping.
		default:
			continue
		}

		text := strings.TrimSpace(firstNonEmptyString(item["text"], item["content"]))
		wrapped := map[string]any{
			"type": "message",
			"role": role,
			"content": []any{
				map[string]any{
					"type": contentType,
					"text": text,
				},
			},
		}
		if id := strings.TrimSpace(firstNonEmptyString(item["id"])); id != "" {
			wrapped["id"] = id
		}
		input[i] = wrapped
		changed = true
	}
	if changed {
		reqBody["input"] = input
	}
	return changed
}
