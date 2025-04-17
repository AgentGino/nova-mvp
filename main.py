import os
import asyncio
import argparse
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import necessary components from other modules
from bedrock_manager import BedrockStreamManager
from audio_streamer import AudioStreamer
from utils import time_it_async
import utils # Import the whole module to modify utils.DEBUG

async def main(debug=False):
    """Main function to run the application."""
    # Set the global DEBUG flag in the utils module
    utils.DEBUG = debug

    stream_manager = None
    audio_streamer = None

    try:
        # Create stream manager
        model_id = os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-sonic-v1:0') # Default if not in .env
        region = os.getenv('BEDROCK_REGION', 'us-east-1') # Default if not in .env
        system_prompt = os.getenv(
            'BEDROCK_SYSTEM_PROMPT',
            "You are a friendly assistant. Keep responses concise."
        ) # Default if not in .env
        voice_id = os.getenv('BEDROCK_VOICE_ID', 'matthew') # Default if not in .env
        
        # Check if required AWS credentials are set (either in .env or environment)
        # if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY') or not os.getenv('AWS_DEFAULT_REGION'):
        #      print("Warning: AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION) not found.")
        #      print("Please set them in the .env file or as environment variables.")
        #      # Decide if you want to exit or proceed with potentially failing AWS client init
        #      # return # Exit if credentials are required
        # The ProfileCredentialsResolver in BedrockStreamManager will handle finding credentials
        # based on AWS_PROFILE or default AWS configuration (~/.aws/credentials, ~/.aws/config).
        
        stream_manager = BedrockStreamManager(
            model_id=model_id, 
            region=region, 
            system_prompt=system_prompt,
            voice_id=voice_id
        )

        # Initialize the stream
        await time_it_async("initialize_stream", stream_manager.initialize_stream)

        # Create audio streamer only after stream is initialized
        audio_streamer = AudioStreamer(stream_manager)

        # This will run until the user presses Enter
        await audio_streamer.start_streaming()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nApplication error: {e}")
        if utils.DEBUG:
            traceback.print_exc()
    finally:
        # Clean up
        print("\nInitiating cleanup...")
        if audio_streamer:
            await audio_streamer.stop_streaming() # This now also handles stream_manager.close()
        elif stream_manager and stream_manager.is_active:
            # If audio_streamer failed to init, ensure stream_manager is closed
            await stream_manager.close()
        print("Cleanup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Nova Sonic Python Streaming')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Set your AWS credentials here or use environment variables
    # Ensure required environment variables are set
    required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
    if not all(os.getenv(var) for var in required_env_vars):
        print("Warning: AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION) not found in environment variables.")
        print("Please set them or configure AWS credentials appropriately.")
        # Optionally exit if credentials are required
        # exit(1) 
    else:
        # Optionally set the region from env var if needed elsewhere, though BedrockManager uses its own region param
        os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION', 'us-east-1') 

    # Run the main function
    asyncio.run(main(debug=args.debug))