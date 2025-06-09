import requests
import json
import os
import time

from termcolor import colored


BASE_URL = "http://localhost:7012"
API_KEY = os.getenv("ADMIN_API_KEY", "admin1234")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def wait_for_service(url, timeout=30):
    """Wait for the service to be available"""
    print(colored("⏳ Waiting for service to be available...", "yellow"))
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/v1/models", headers=HEADERS, timeout=5)
            if response.status_code == 200:
                print(colored("✓ Service is ready!", "green"))
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    print(colored(f"✗ Service failed to start within {timeout} seconds", "red"))
    return False


def test_service_is_running():
    """Test that the service is running and accessible"""
    assert wait_for_service(BASE_URL), "Service is not running or not accessible"


def test_all_models_chat_completions():
    """Test chat completions for all available models with stream=False"""

    print(colored("\n🚀 Starting LLM Portal Model Tests", "cyan", attrs=["bold"]))
    print(colored("=" * 50, "cyan"))

    # First, get all available models
    print(colored("📋 Fetching available models...", "blue"))
    models_response = requests.get(f"{BASE_URL}/v1/models", headers=HEADERS)

    assert models_response.status_code == 200, f"Failed to get models: {models_response.text}"

    models_data = models_response.json()
    assert models_data["object"] == "list"
    assert "data" in models_data

    available_models = models_data["data"]
    assert len(available_models) > 0, "No models available for testing"

    print(colored(f"Found {len(available_models)} models to test:", "blue", attrs=["bold"]))
    for model in available_models:
        print(colored(f"  • {model['id']}", "blue"))

    # Test chat completion for each model
    test_messages = [
        {
            "role": "user",
            "content": "Answer with Yes or No. Are you an LLM?"
        }
    ]

    successful_tests = 0
    failed_tests = []

    print(colored("\n🧪 Testing models...", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))

    for model_info in available_models:
        model_id = model_info["id"]

        chat_request = {
            "model": model_id,
            "messages": test_messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 50
        }

        try:
            print(colored(f"🔄 Testing model: {model_id}...", "yellow"))

            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                headers=HEADERS,
                json=chat_request,
                timeout=30
            )

            if response.status_code == 200:
                response_text = response.text

                try:
                    response_data = json.loads(response_text)

                    try:
                        assert "choices" in response_data, f"No 'choices' in response for {model_id}"
                        assert len(response_data["choices"]) > 0, f"Empty choices for {model_id}"
                        assert "message" in response_data["choices"][0], f"No 'message' in choice for {model_id}"
                        assert "content" in response_data["choices"][0]["message"], f"No 'content' in message for {model_id}"

                        content = response_data["choices"][0]["message"]["content"]
                        assert content, f"Empty content for {model_id}"
                    except AssertionError as e:
                        print(colored(f"❌ Model {model_id}: VALIDATION ERROR", "red", attrs=["bold"]))
                        print(colored(f"   🔍 Error: {str(e)}", "red"))
                        print(colored(f"   📝 Response: {response_text}", "red"))
                        raise

                    successful_tests += 1
                    print(colored(f"✅ Model {model_id}: SUCCESS", "green", attrs=["bold"]))
                    print(colored(f"   💬 Response: {content[:100]}{'...' if len(content) > 100 else ''}", "green"))

                except json.JSONDecodeError as e:
                    failed_tests.append({
                        "model": model_id,
                        "error": f"JSON decode error: {str(e)}",
                        "response": response_text[:200]
                    })
                    print(colored(f"❌ Model {model_id}: JSON DECODE ERROR", "red", attrs=["bold"]))
                    print(colored(f"   🔍 Error: {str(e)}", "red"))

            else:
                failed_tests.append({
                    "model": model_id,
                    "status_code": response.status_code,
                    "response": response.text[:500]
                })
                print(colored(f"❌ Model {model_id}: FAILED (status: {response.status_code})", "red", attrs=["bold"]))
                print(
                    colored(f"   🔍 Response: {response.text[:200]}{'...' if len(response.text) > 200 else ''}", "red"))

        except requests.exceptions.Timeout:
            failed_tests.append({
                "model": model_id,
                "error": "Request timeout"
            })
            print(colored(f"⏰ Model {model_id}: TIMEOUT", "red", attrs=["bold"]))

        except Exception as e:
            failed_tests.append({
                "model": model_id,
                "error": str(e)
            })
            print(colored(f"💥 Model {model_id}: EXCEPTION - {str(e)}", "red", attrs=["bold"]))

    # Print summary
    print(colored("\n" + "=" * 60, "cyan"))
    print(colored("📊 TEST SUMMARY", "cyan", attrs=["bold"]))
    print(colored("=" * 60, "cyan"))

    print(colored(f"📈 Total models tested: {len(available_models)}", "white", attrs=["bold"]))
    print(colored(f"✅ Successful: {successful_tests}", "green", attrs=["bold"]))
    print(colored(f"❌ Failed: {len(failed_tests)}", "red", attrs=["bold"]))

    if failed_tests:
        print(colored("\n🔍 Failed tests details:", "red", attrs=["bold"]))
        for i, failure in enumerate(failed_tests, 1):
            print(colored(f"\n{i}. Model: {failure['model']}", "red", attrs=["bold"]))
            if 'status_code' in failure:
                print(colored(f"   📊 Status: {failure['status_code']}", "red"))
            if 'error' in failure:
                print(colored(f"   ⚠️  Error: {failure['error']}", "red"))
            if 'response' in failure:
                print(colored(f"   📝 Response: {failure['response']}", "red"))

    success_rate = successful_tests / len(available_models)

    assert success_rate == 1, f"Some models failed the test: {failed_tests}"

    print(colored("\n🎊 All tests completed successfully!", "green", attrs=["bold"]))


if __name__ == "__main__":
    # Run the tests
    test_service_is_running()
    test_all_models_chat_completions()
    print(colored("🏆 All tests passed!", "green", attrs=["bold"]))
