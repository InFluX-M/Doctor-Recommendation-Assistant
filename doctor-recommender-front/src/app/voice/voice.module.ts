import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VoiceRecorderComponent } from './voice-recorder/voice-recorder.component';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [VoiceRecorderComponent],
  imports: [CommonModule, SharedModule],
})
export class VoiceModule {}
