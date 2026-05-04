import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from pipeline import call_bot
from router import route

DATA_PATH = Path(__file__).parent.parent / "server"/ "data" / "conversations.json"


def evaluate_single_turn(conversations):
    """Evaluates one-turn conversations"""
    intent_correct = 0
    route_correct = 0
    total = len(conversations)

    print(f"\n--- Single-Turn ---")
    print(f"{'ID':<12} {'INTENT OK':<12} {'ROUTE OK':<12} {'ENTITIES':<12} {'URGENCY': <12} {'CONFIDENCE':<12} {'INTENT'}")

    for conv in conversations:
        msg = conv["message"]
        expected_intent = conv["expected_intent"]
        expected_route = conv["expected_route"]
        expected_entities = conv["expected_entities"]
        set_of_expected_entities = set(expected_entities.keys())
        expected_urgency = expected_entities.get("urgency", "unknown")

        try:
            ai_result = call_bot(msg)
        except Exception as exc:
            print(f"{conv['id']:<12} ERROR: {exc}")
            continue

        predicted_intent = ai_result.get("intent", "")
        predicted_entities = ai_result.get("entities", {})
        set_of_predicted_entities = set()
        for entity in predicted_entities.keys():
            if predicted_entities[entity]:
                set_of_predicted_entities.add(entity)

        confidence = float(ai_result.get("confidence", 0))
        predicted_urgency = predicted_entities.get("urgency", "unknown")

        predicted_route, _, _= route(predicted_intent, predicted_entities, confidence, msg)

        correct_intent = predicted_intent == expected_intent
        correct_route = predicted_route == expected_route
        correct_entities = set_of_expected_entities == set_of_predicted_entities
        correct_urgency = predicted_urgency == expected_urgency

        if correct_intent:
            intent_correct += 1
        if correct_route:
            route_correct += 1

        tick_i = "✓" if correct_intent else "✗"
        tick_r = "✓" if correct_route else "✗"
        tick_e = "✓" if correct_entities else "✗"
        tick_u = "✓" if correct_urgency else "✗"
        print(
            f"{conv['id']:<12} {tick_i + ' intent':<12} {tick_r + ' route':<12} {tick_e + ' entities':<12} {tick_u + ' urgency':<12}"
            f"{confidence:<12.0%} {predicted_intent}"
        )

    print(f"\nIntent accuracy : {intent_correct}/{total} = {intent_correct/total:.0%}")
    print(f"Route accuracy  : {route_correct}/{total} = {route_correct/total:.0%}")


def evaluate_multi_turn(conversations):
    """Evaluates multi-turn conversations"""
    intent_correct = 0
    route_correct = 0
    total_turns = 0

    print(f"\n--- Multi-Turn ---")
    print(f"{'ID':<16} {'TURN':<6} {'INTENT OK':<12} {'ROUTE OK':<12} {'CONFIDENCE':<12} {'INTENT'}")

    for conv in conversations:
        previous_context = None

        for turn in conv["turns"]:
            msg = turn["message"]
            expected_intent = turn["expected_intent"]
            expected_route = turn["expected_route"]

            try:
                ai_result = call_bot(msg, previous_context)
            except Exception as exc:
                print(f"{conv['id']:<16} turn {turn['turn']}  ERROR: {exc}")
                continue

            predicted_intent = ai_result.get("intent", "")
            predicted_entities = ai_result.get("entities", {})
            confidence = float(ai_result.get("confidence", 0))
            predicted_route, _, _ = route(predicted_intent, predicted_entities, confidence, msg)

            correct_intent = predicted_intent == expected_intent
            correct_route = predicted_route == expected_route

            if correct_intent: intent_correct += 1
            if correct_route: route_correct += 1
            total_turns += 1

            tick_i = "✓" if correct_intent else "✗"
            tick_r = "✓" if correct_route else "✗"
            print(
                f"{conv['id']:<16} t{turn['turn']:<5} {tick_i + ' intent':<12} {tick_r + ' route':<12}"
                f"{confidence:<12.0%} {predicted_intent}"
            )

            # Build context for next turn from actual model output
            history = (previous_context or {}).get("conversation_history", [])
            previous_context = {
                "conversation_history": history + [msg],
                "previous_json": ai_result
            }

    print(f"\nIntent accuracy : {intent_correct}/{total_turns} = {intent_correct/total_turns:.0%}")
    print(f"Route accuracy  : {route_correct}/{total_turns} = {route_correct/total_turns:.0%}")


def evaluate():
    """Evaluates chatbot and routing to see if intent and routing are correctly captured"""
    with open(DATA_PATH) as f:
        conversations = json.load(f)

    single = [c for c in conversations if c.get("type") != "multi_turn"]
    multi  = [c for c in conversations if c.get("type") == "multi_turn"]

    if single:
        pass
        #evaluate_single_turn(single)
    if multi:
        evaluate_multi_turn(multi)


if __name__ == "__main__":
    evaluate()