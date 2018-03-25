import { Component } from '@angular/core';
import { NavController, ViewController } from 'ionic-angular';

/*
  Generated class for the SigninPage page.

  See http://ionicframework.com/docs/v2/components/#navigation for more info on
  Ionic pages and navigation.
*/
@Component({
  templateUrl: 'build/pages/signin/signin.html',
})
export class SigninPage {
  public email: string;
  public username: string;
  constructor(private navCtrl: NavController, private view: ViewController) {

  }
  
  signin(){
    localStorage.setItem('user', this.email);
    localStorage.setItem('username', this.username);
    console.log(localStorage.getItem('username'));
    this.view.dismiss({email: this.email, username: this.username});
  }
}
