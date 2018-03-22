import { Injectable, Pipe } from '@angular/core';

/*
  Generated class for the D2S pipe.

  See https://angular.io/docs/ts/latest/guide/pipes.html for more info on
  Angular 2 Pipes.
*/
@Pipe({
  name: 'd2s'
})
@Injectable()
export class D2S {
  /*
    Takes a value and makes it lowercase.
   */
  transform(value: any, args: any[]) {
    return new Date(parseInt(value.$date));;
  }
}
