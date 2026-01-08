print("Testing backend setup...")

try:
    import flask
    print(f"✓ Flask: {flask.__version__}")
except ImportError:
    print("✗ Flask not installed")

try:
    import numpy
    print(f"✓ NumPy: {numpy.__version__}")
except ImportError:
    print("✗ NumPy not installed")

try:
    import moviepy
    print("✓ MoviePy installed")
except ImportError:
    print("✗ MoviePy not installed")

try:
    from tts_engine import tts_engine
    print("✓ TTS engine initialized")
    
    # Test TTS
    test_text = "Xin chào, đây là kiểm tra hệ thống."
    result = tts_engine.text_to_speech(test_text)
    print("✓ TTS test successful")
    
except Exception as e:
    print(f"✗ TTS error: {e}")

print("\nSetup test completed!")