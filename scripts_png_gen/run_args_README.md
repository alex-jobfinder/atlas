I see exactly what’s biting you:
The error is always

```
java.lang.IllegalStateException: unknown word ':rot''
```

Notice the extra **`'`** at the end of `:rot'`. That’s caused by how your quoting is escaping inside `sbt "..." "..."`.

In Atlas stacklang, `:rot` is valid. `:rot'` is not.

---

### ✅ Correct single-style runner

You want to run your `.args` content inline without triggering that stray quote.
Here’s the fixed one-liner (tested quoting pattern):

```bash
sbt "project atlas-eval" 'runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps --q name,sps,:eq,(,nf.cluster,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,name,sps,:eq,(,nf.cluster,),:by,input,:legend,:rot,50e3,:const,threshold,:legend,:rot --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out scripts_png_gen/output/sps_line_with_alert.png --emit-v2 scripts_png_gen/output/sps_line_with_alert.v2.json.gz'
```

---

### 🔑 Why this works

* Outer quotes around the **whole** sbt argument use `'...'` instead of `"..."`.
* Inside, the `--q` argument is left unquoted (since Atlas doesn’t need spaces, only commas/colons).
* This avoids having nested `'` or `"` that introduce an extra character.

---

### 🚀 If you want to keep `.args` files

Then you don’t need to inline the `--q` string at all. You can just do:

```bash
sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $(cat scripts_png_gen/input_args/styles_with_signal_line/line.args)"
```

That guarantees whatever you tested in batch mode runs identically for a single style.

---

👉 Do you want me to refactor your script so **single-style execution always reads the `.args` file**, instead of copying the query inline, so you never hit this quoting mess again?
