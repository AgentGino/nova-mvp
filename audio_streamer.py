import asyncio
import pyaudio
import traceback

from utils import debug_print, time_it, time_it_async
from config import FORMAT, CHANNELS, INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE, CHUNK_SIZE
# BedrockStreamManager is imported in main.py and passed to the constructor

class AudioStreamer:
    """Handles continuous microphone input and audio output using separate streams."""
    
    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.is_streaming = False
        self.loop = asyncio.get_event_loop()

        # Initialize PyAudio
        debug_print("AudioStreamer Initializing PyAudio...")
        self.p = time_it("AudioStreamerInitPyAudio", pyaudio.PyAudio)
        debug_print("AudioStreamer PyAudio initialized")

        # Initialize separate streams for input and output
        self.input_stream = None
        self.output_stream = None
        self._initialize_audio_streams()

    def _initialize_audio_streams(self):
        """Initializes PyAudio input and output streams."""
        try:
            # Input stream with callback for microphone
            debug_print("Opening input audio stream...")
            self.input_stream = time_it("AudioStreamerOpenInputAudio", lambda  : self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=INPUT_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.input_callback
            ))
            debug_print("Input audio stream opened")

            # Output stream for direct writing (no callback)
            debug_print("Opening output audio stream...")
            self.output_stream = time_it("AudioStreamerOpenOutputAudio", lambda  : self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=OUTPUT_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE
            ))
            debug_print("Output audio stream opened")
        except Exception as e:
            print(f"Error initializing audio streams: {e}")
            traceback.print_exc()
            # Clean up if streams failed to open
            if self.input_stream:
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.close()
            if self.p:
                self.p.terminate()
            raise # Re-raise the exception to signal failure

    def input_callback(self, in_data, frame_count, time_info, status):
        """Callback function that schedules audio processing in the asyncio event loop"""
        if self.is_streaming and in_data:
            # Schedule the task in the event loop
            asyncio.run_coroutine_threadsafe(
                self.process_input_audio(in_data), 
                self.loop
            )
        return (None, pyaudio.paContinue)

    async def process_input_audio(self, audio_data):
        """Process a single audio chunk directly"""
        try:
            # Send audio to Bedrock immediately
            self.stream_manager.add_audio_chunk(audio_data)
        except Exception as e:
            if self.is_streaming:
                print(f"Error processing input audio: {e}")
    
    async def play_output_audio(self):
        """Play audio responses from Nova Sonic"""
        while self.is_streaming:
            try:
                # Check for barge-in flag
                if self.stream_manager.barge_in:
                    # Clear the audio queue
                    while not self.stream_manager.audio_output_queue.empty():
                        try:
                            self.stream_manager.audio_output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    self.stream_manager.barge_in = False
                    # Small sleep after clearing
                    await asyncio.sleep(0.05)
                    continue
                
                # Get audio data from the stream manager's queue
                audio_data = await asyncio.wait_for(
                    self.stream_manager.audio_output_queue.get(),
                    timeout=0.1
                )
                
                if audio_data and self.is_streaming and self.output_stream and self.output_stream.is_active():
                    # Write directly to the output stream in smaller chunks
                    chunk_size = CHUNK_SIZE  # Use the same chunk size as the stream
                    
                    # Write the audio data in chunks to avoid blocking too long
                    for i in range(0, len(audio_data), chunk_size):
                        if not self.is_streaming:
                            break
                        
                        end = min(i + chunk_size, len(audio_data))
                        chunk = audio_data[i:end]
                        
                        # Create a new function that captures the chunk by value
                        def write_chunk(data):
                            # Ensure stream is still active before writing
                            if self.output_stream and self.output_stream.is_active():
                                return self.output_stream.write(data)
                            return None # Indicate writing didn't happen
                        
                        # Pass the chunk to the function
                        await asyncio.get_event_loop().run_in_executor(None, write_chunk, chunk)
                        
                        # Brief yield to allow other tasks to run
                        await asyncio.sleep(0.001)
                    
            except asyncio.TimeoutError:
                # No data available within timeout, just continue
                continue
            except Exception as e:
                if self.is_streaming:
                    print(f"Error playing output audio: {str(e)}")
                    traceback.print_exc()
                await asyncio.sleep(0.05)
    
    async def start_streaming(self):
        """Start streaming audio."""
        if self.is_streaming:
            return
        
        print("Starting audio streaming. Speak into your microphone...")
        print("Press Enter to stop streaming...")
        
        # Send audio content start event
        await time_it_async("send_audio_content_start_event", lambda : self.stream_manager.send_audio_content_start_event())
        
        self.is_streaming = True
        
        # Start the input stream if not already started and initialized
        if self.input_stream and not self.input_stream.is_active():
            self.input_stream.start_stream()
        
        # Start processing tasks
        self.output_task = asyncio.create_task(self.play_output_audio())
        
        # Wait for user to press Enter to stop
        await asyncio.get_event_loop().run_in_executor(None, input)
        
        # Once input() returns, stop streaming
        await self.stop_streaming()
    
    async def stop_streaming(self):
        """Stop streaming audio."""
        if not self.is_streaming:
            return
            
        self.is_streaming = False
        print("Stopping audio streaming...")

        # Cancel the tasks
        tasks = []        
        if hasattr(self, 'output_task') and self.output_task and not self.output_task.done():
            self.output_task.cancel()
            tasks.append(self.output_task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop and close the streams gracefully
        if self.input_stream:
            try:
                if self.input_stream.is_active():
                    self.input_stream.stop_stream()
                self.input_stream.close()
                debug_print("Input audio stream closed.")
            except Exception as e:
                print(f"Error closing input stream: {e}")
        
        if self.output_stream:
            try:
                if self.output_stream.is_active():
                    # Wait for buffer to finish playing before stopping?
                    # self.output_stream.stop_stream() # Can sometimes cut off audio
                    pass 
                self.output_stream.close()
                debug_print("Output audio stream closed.")
            except Exception as e:
                print(f"Error closing output stream: {e}")

        # Terminate PyAudio instance
        if self.p:
            self.p.terminate()
            debug_print("PyAudio terminated.")
        
        # Close the Bedrock stream manager
        await self.stream_manager.close()
        debug_print("Bedrock stream manager closed.") 