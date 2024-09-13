import { NgModule } from '@angular/core';
import { CommonModule, NgOptimizedImage } from '@angular/common';
import { HeaderComponent } from './header/header.component';
import { NzFlexModule } from 'ng-zorro-antd/flex';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { NzButtonModule } from 'ng-zorro-antd/button';

@NgModule({
  declarations: [HeaderComponent, HomeComponent],
  exports: [HeaderComponent, HomeComponent],
  imports: [
    CommonModule,
    NzFlexModule,
    RouterLink,
    RouterLinkActive,
    NgOptimizedImage,
    NzButtonModule,
  ],
})
export class SharedModule {}
