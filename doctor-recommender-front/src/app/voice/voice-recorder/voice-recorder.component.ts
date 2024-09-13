import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import WaveSurfer from 'wavesurfer.js';
import RecordPlugin from 'wavesurfer.js/plugins/record';

@Component({
  selector: 'app-voice-recorder',
  templateUrl: './voice-recorder.component.html',
  styleUrl: './voice-recorder.component.scss',
})
export class VoiceRecorderComponent implements OnInit {
  @ViewChild('mic', { static: true }) micElement!: ElementRef;
  @ViewChild('recordings', { static: true }) recordingsElement!: ElementRef;
  @ViewChild('progress', { static: true }) progressElement!: ElementRef;
  @ViewChild('pauseButton', { static: true }) pauseButtonElement!: ElementRef;
  @ViewChild('recButton', { static: true }) recButtonElement!: ElementRef;
  @ViewChild('micSelect', { static: true }) micSelectElement!: ElementRef;

  wavesurfer: any;
  record: any;
  scrollingWaveform = false;

  ngOnInit(): void {
    this.createWaveSurfer();
    this.loadMicrophoneOptions();
  }

  createWaveSurfer() {
    if (this.wavesurfer) {
      this.wavesurfer.destroy();
    }

    this.wavesurfer = WaveSurfer.create({
      container: this.micElement.nativeElement,
      waveColor: 'rgb(200, 0, 200)',
      progressColor: 'rgb(100, 0, 100)',
    });

    this.record = this.wavesurfer.registerPlugin(
      RecordPlugin.create({
        scrollingWaveform: this.scrollingWaveform,
        renderRecordedAudio: false,
      }),
    );

    this.record.on('record-end', (blob: Blob) => this.renderRecording(blob));

    this.pauseButtonElement.nativeElement.style.display = 'none';
    this.recButtonElement.nativeElement.textContent = 'Record';
  }

  renderRecording(blob: Blob) {
    const recordedUrl = URL.createObjectURL(blob);
    const container = this.recordingsElement.nativeElement;

    const wavesurfer = WaveSurfer.create({
      container,
      waveColor: 'rgb(200, 100, 0)',
      progressColor: 'rgb(100, 50, 0)',
      url: recordedUrl,
    });

    const button = container.appendChild(document.createElement('button'));
    button.textContent = 'Play';
    button.onclick = () => wavesurfer.playPause();
    wavesurfer.on('pause', () => (button.textContent = 'Play'));
    wavesurfer.on('play', () => (button.textContent = 'Pause'));

    const link = container.appendChild(document.createElement('a'));
    link.href = recordedUrl;
    link.download = `recording.${blob.type.split(';')[0].split('/')[1] || 'webm'}`;
    link.textContent = 'Download recording';
  }

  loadMicrophoneOptions() {
    RecordPlugin.getAvailableAudioDevices().then(
      (devices: MediaDeviceInfo[]) => {
        devices.forEach((device) => {
          const option = document.createElement('option');
          option.value = device.deviceId;
          option.text = device.label || device.deviceId;
          this.micSelectElement.nativeElement.appendChild(option);
        });
      },
    );
  }

  toggleRecording() {
    if (this.record.isRecording() || this.record.isPaused()) {
      this.record.stopRecording();
      this.recButtonElement.nativeElement.textContent = 'Record';
      this.pauseButtonElement.nativeElement.style.display = 'none';
      return;
    }

    const deviceId = this.micSelectElement.nativeElement.value;
    this.record.startRecording({ deviceId }).then(() => {
      this.recButtonElement.nativeElement.textContent = 'Stop';
      this.pauseButtonElement.nativeElement.style.display = 'inline';
    });
  }

  togglePause() {
    if (this.record.isPaused()) {
      this.record.resumeRecording();
      this.pauseButtonElement.nativeElement.textContent = 'Pause';
    } else {
      this.record.pauseRecording();
      this.pauseButtonElement.nativeElement.textContent = 'Resume';
    }
  }

  updateProgress(time: number) {
    const formattedTime = [
      Math.floor((time % 3600000) / 60000), // minutes
      Math.floor((time % 60000) / 1000), // seconds
    ]
      .map((v) => (v < 10 ? '0' + v : v))
      .join(':');
    this.progressElement.nativeElement.textContent = formattedTime;
  }

  onScrollingWaveformChange(event: Event) {
    this.scrollingWaveform = (event.target as HTMLInputElement).checked;
    this.createWaveSurfer();
  }
}
