import { KernelBase } from "@basthon/kernel-base";

const PYODIDE_VERSION = "0.23.2";

declare global {
  interface Window {
    loadPyodide?: any;
    pyodide?: any;
  }
}

/**
 * A Python kernel that satisfies Basthon's API.
 */
export class KernelPython3 extends KernelBase {
  /**
   * Where to find pyodide.js (private).
   */
  private _pyodideURLs = [
    `https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/pyodide.js`,
  ];
  private __kernel__: any = null;
  public pythonVersion: string = "";

  constructor(options: any) {
    super(options);
    // for locally installed Pyodide
    this._pyodideURLs.unshift(`${this.basthonRoot()}/pyodide/pyodide.js`);
    this._pyodideURLs = options?.pyodideURLs ?? this._pyodideURLs;
  }

  /**
   * Get the URL of Basthon modules dir.
   */
  public basthonModulesRoot(absolute: boolean = false) {
    return this.basthonRoot(absolute) + "/modules";
  }

  public language() {
    return "python3";
  }
  public languageName() {
    return "Python 3";
  }
  public moduleExts() {
    return ["py"];
  }

  /**
   * What to do when loaded (private).
   */
  async _onload() {
    const pyodide = window.pyodide;
    // reformat repodata
    const packages = pyodide._api.repodata_packages;
    for (let p of Object.keys(packages)) {
      const item = packages[p];
      item.file_name = item.file_name.replace(
        "{basthonRoot}",
        this.basthonRoot(true)
      );
    }
    // get the version of Python from Python
    this.pythonVersion = pyodide.runPython(
      "import platform ; platform.python_version()"
    );
    // load basthon and get kernel
    await pyodide.loadPackage("basthon");
    this.__kernel__ = pyodide.pyimport("basthon").__kernel__;
  }

  /**
   * Start the Basthon kernel asynchronously.
   */
  public async launch() {
    let pyodideURL: string = this._pyodideURLs[0];
    for (let url of this._pyodideURLs) {
      url = url.replace("{PYODIDE_VERSION}", PYODIDE_VERSION);
      try {
        const response = await fetch(url, { method: "HEAD" });
        if (response.ok) {
          pyodideURL = url;
          break;
        }
      } catch (e) {}
    }

    try {
      await KernelPython3.loadScript(pyodideURL);
    } catch (error) {
      console.log(error);
      console.error("Can't load pyodide.js");
      throw error;
    }

    if (window.loadPyodide == null) {
      console.log("window.loadPyodide is null!");
      throw new Error("Can't load pyodide.js");
    }

    try {
      // loading with custom repodata.json
      window.pyodide = await window.loadPyodide({
        lockFileURL: this.basthonRoot() + "/repodata.json",
      });
    } catch (error) {
      console.log(error);
      console.error("Can't load Python from Pyodide");
      throw error;
    }
    await this._onload();
  }

  /**
   * Execution count getter overload.
   */
  public get execution_count() {
    return this.__kernel__.execution_count();
  }

  /**
   * Basthon async code evaluation function.
   */
  public async evalAsync(
    code: string,
    outCallback: (_: string) => void,
    errCallback: (_: string) => void,
    data: any = null
  ): Promise<any> {
    if (typeof outCallback === "undefined") {
      outCallback = function (text) {
        console.log(text);
      };
    }
    if (typeof errCallback === "undefined") {
      errCallback = function (text) {
        console.error(text);
      };
    }
    // dependencies are loaded by eval
    const proxy = await this.__kernel__.eval(
      code,
      outCallback,
      errCallback,
      data
    );
    // when an error occures, proxy should be the error message
    if (!window.pyodide.isPyProxy(proxy)) throw proxy;
    const res = proxy.toJs({
      create_proxies: false,
      dict_converter: Object.fromEntries,
    });
    proxy.destroy();
    return res;
  }

  /**
   * Restart the kernel.
   */
  public restart() {
    return this.__kernel__.restart();
  }

  /**
   * Put a file on the local (emulated) filesystem.
   */
  public async putFile(filename: string, content: ArrayBuffer) {
    this.__kernel__.put_file(filename, content);
  }

  /**
   * Put an importable module on the local (emulated) filesystem
   * and load dependencies.
   */
  public async putModule(filename: string, content: ArrayBuffer) {
    return await this.__kernel__.put_module(filename, content);
  }

  /**
   * List modules launched via putModule.
   */
  public userModules() {
    const proxy = this.__kernel__.user_modules();
    if (!window.pyodide.isPyProxy(proxy)) return proxy;
    const res = proxy.toJs();
    proxy.destroy();
    return res;
  }

  /**
   * Get a file content from the VFS.
   */
  public getFile(path: string): Uint8Array {
    return this.__kernel__.get_file(path).toJs();
  }

  /**
   * Get a user module file content.
   */
  public getUserModuleFile(filename: string): Uint8Array {
    return this.__kernel__.get_user_module_file(filename).toJs();
  }

  /**
   * Is the source ready to be evaluated or want we more?
   * Usefull to set ps1/ps2 for teminal prompt.
   */
  public more(source: string) {
    return this.__kernel__.more(source);
  }

  /**
   * Mimic the CPython's REPL banner.
   */
  public banner() {
    /* We don't return this.__kernel__.banner();
     * since the banner should be available ASAP.
     * In tests, we check this.banner() ===  this.__kernel__.banner().
     */
    return `Python 3.11.2 (main, May  3 2023 04:00:05) on WebAssembly/Emscripten\nType \"help\", \"copyright\", \"credits\" or \"license\" for more information.`;
  }

  /**
   * Complete a code at the end (usefull for tab completion).
   *
   * Returns an array of two elements: the list of completions
   * and the start index.
   */
  public complete(code: string) {
    const proxy = this.__kernel__.complete(code);
    if (!window.pyodide.isPyProxy(proxy)) return proxy;
    const res = proxy.toJs();
    proxy.destroy();
    return res;
  }

  /**
   * Change current directory (Python's virtual FS).
   */
  public chdir(path: string) {
    window.pyodide._module.FS.chdir(path);
  }

  /**
   * Create directory (Python's virtual FS).
   */
  public mkdir(path: string) {
    window.pyodide._module.FS.mkdir(path);
  }
}
