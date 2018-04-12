import { Component } from '@angular/core';
import { NavController, NavParams } from 'ionic-angular';

/*
  Generated class for the ParticipantsPage page.

  See http://ionicframework.com/docs/v2/components/#navigation for more info on
  Ionic pages and navigation.
*/
@Component({
  templateUrl: 'build/pages/participants/participants.html',
})
export class ParticipantsPage {
  public participants: any;
  
  constructor(private navCtrl: NavController, private params: NavParams) {
    this.participants = this.params.get('participants')  ;
    console.log(this.participants);
  }

}
