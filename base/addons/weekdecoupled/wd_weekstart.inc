* WeekDecoupled add-on (docs/adr/0006): solve only the week IS3LOOPSET.
* The storage hooks (wd_q*.inc) make every storage end the week at its starting level.
IS3(S) = NO;
IS3(IS3LOOPSET) = YES;
IS3_NEXT(S) = NO;
IS3_NEXT(IS3LOOPSET) = YES;
IS3_ONLYNEXT(S) = NO;
