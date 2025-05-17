# Sapflux Programs

This is my extremely stupid program for generating firmware for running implexx sapflux sensors on CR200-series dataloggers.

I set out with the bold, radical goals of:

* I should be able to write this code in my usual development environment.
* I should log all the relevant info that comes off of the sensors.
* I should do this in a way that is relatively flexible, e.g. it can scale to arbitrary N sensors.

Towards the first point, I wrote [crbrs](https://www.github.com/rileyleff.crbrs), available on [crates.io](https://crates.io/crates/crbrs). It allows you to install campbell scientific compilers, hosted in a separate repository [here](https://github.com/RileyLeff/campbell-scientific-compilers). You can use it compile CRBasic code for any supported datalogger on MacOS, Linux, or Windows, without touching the Campbell software that is incompatible with modern dev tools and is exclusive to windows.

Towards the second point, I found that Campbell somewhat arbitrarily limits us to 16 columns max per table. I count 22 things i'm interested in measuring off of each sensor. You can have N > 1 tables though ... so why is there a column limit? Smells like lazy engineering to me. I'm not going to split data across N > 1 tables per sensor. If you end up with a very large number of tables and you need to change their file locations (as we do at each field collection, after learning the hard way about newly corrupt data overwriting previous healthy data) one at a time, it becomes extremely cumbersome and time-consuming to manage in the field. I'm cooked here.

Towards the third point, it seems like there's no way to dynamically generate tables based on a variable. So I just wrote a little python script to generate the static CRBasic code dynamically. Lol. Everything about this is stupid.

## How-To

If for some reason you have the misfortune of relying on this code, you can generate a CRBasic sap flux file as follows:

* Clone this repo to your local filesystem
* Make sure generate_crbasic.py is executable, e.g.
  
```bash
chmod +x generate_crbasic.py
```

* Run the script, providing these arguments:
  * (optional) -o: file path to save the generated crbasic code. If this isn't provided, it just prints to stdout.
  * -n: number of sensors to generate for. Can be 1 to 62 (e.g. sdi12 address space 0-9, a-z, A-Z).
  * -t: number of minutes in between measurements. Can be 15 or greater (less than 15 risks overheating sensor components).

```bash
./generate_crbasic.py -o generated.cr2 -n 3 -t 30 # if you have uv installed like a chad
python3 generate_crbasic.py -o generated.cr2 -n 3 -t 30 # if you're some kind of neanderthal
```

* If you have `crbrs` installed, you can compile the generated file:

```bash
# assuming you have a .cr2 -> cr2comp file association set up in your config
crbrs compile generated.cr2
```

See the crbrs docs if you want to install.

Thanks big dawgs lmk if you have any questions.
