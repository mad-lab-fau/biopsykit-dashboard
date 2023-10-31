# import param
# from panel.reactive import ReactiveHTML
#
#
# class ClientSideFileInput(ReactiveHTML):
#     fileContent = None
#     value = param.Array()
#     fileName = param.String()
#
#     _template = """
#         <input type="file" id="input" onclick='${script("select")}' />
#     """
#
#     _scripts = {
#         "render": """
#         """,
#         "select": """
#             // store a reference to our file handle
#             let fileHandle;
#             const options = {
#                 multiple: true,
#                 types: [
#                     {
#                         description: 'Files to analyze',
#                         accept: {
#                         'text/plain': ['.bin','.csv','.xlsx','.vcf'],
#                         },
#                     },
#                 ],
#             };
#             async function getFile() {
#                 console.log("hi");
#                 [fileHandle] = await window.showOpenFilePicker();
#                 console.log("hi2");
#                 console.log(fileHandle);
#                 if (fileHandle.kind === 'file') {
#                     //run file code
#                     console.log(fileHandle.name);
#                     const file = await fileHandle.getFile();
#                     //console.log(file);
#                     let contents = await file.arrayBuffer();
#                     let arr = new Uint8Array(contents);
#                     //console.log(arr);
#                     data.value = arr;
#                     data.fileName = fileHandle.name;
#                 }
#
#             }
#
#             getFile();
#         """,
#     }
#
#
# class ClientSideDirectoryInput(ReactiveHTML):
#     fileContent = None
#     value = param.Dynamic()
#     fileName = param.String()
#     directoryName = param.String()
#
#     _template = """
#         <input type="file" id="input" onclick='${script("select")}' />
#     """
#
#     _scripts = {
#         "render": """
#         """,
#         "select": """
#             async function getFiles() {
#                 // store a reference to our file handle
#                 const dirHandle = await window.showDirectoryPicker();
#                 const promises = [];
#                 for await (const entry of dirHandle.values()) {
#                     if (entry.kind !== 'file') {
#                         continue;
#                     }
#                     const file = await entry.getFile();
#                     let fileName = file.name;
#                     if(fileName.endsWith('.bin') || fileName.endsWith('.csv')){
#                         console.log(fileName);
#                         let contents = await file.arrayBuffer();
#                         let arr = new Uint8Array(contents);
#                         const data = {
#                             name: fileName,
#                             fileContent: arr
#                         };
#                         promises.push(data);
#                     }
#                 }
#                 console.log(await Promise.all(promises));
#                 data.value = promises;
#             }
#             getFiles();
#             console.log('Done');
#         """,
#     }


# const
# dirHandle = await showDirectoryPicker();
#
# if ((await dirHandle.queryPermission({mode: "readwrite"})) !== "granted") {
# if (
# (await dirHandle.requestPermission({mode: "readwrite"})) != = "granted"
# ) {
#     throw
# Error("Unable to read and write directory");
# }
# }
# let
# pyodide = await loadPyodide();
# const
# nativefs = await pyodide.mountNativeFS("/mount_dir", dirHandle);
# console.log(nativefs);
# pyodide.runPython(`
# import os
# from pathlib import Path
#
# print(os.listdir('/mount_dir'))
#
# `);

#        <input type="file" id="input" onclick='${script("select")}' />
#             importScripts("https://cdn.jsdelivr.net/pyodide/v0.21.3/full/pyodide.js");
