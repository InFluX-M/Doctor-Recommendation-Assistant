import { NgModule } from '@angular/core';
import { CommonModule, NgOptimizedImage } from '@angular/common';
import { VoiceRecorderComponent } from './voice-recorder/voice-recorder.component';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NzFlexModule } from 'ng-zorro-antd/flex';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { FormsModule } from '@angular/forms';

@NgModule({
  declarations: [VoiceRecorderComponent],
  exports: [VoiceRecorderComponent],
  imports: [
    CommonModule,
    NzFlexModule,
    RouterLink,
    RouterLinkActive,
    NgOptimizedImage,
    NzButtonModule,
    NzSelectModule,
    FormsModule,
  ],
})
export class VoiceModule {}
