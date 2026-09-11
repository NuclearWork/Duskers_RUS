using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace DllExtractor
{
    class Program
    {
        static void Main(string[] args)
        {
            string dllPath = @"Z:\SteamLibrary\steamapps\common\Duskers\Duskers_Data\Managed\Assembly-CSharp.dll";
            string outPath = @"C:\Users\user\Documents\GITHUB\Duskers_RUS\Exported_EN\dll_strings_en.json";

            var module = ModuleDefinition.ReadModule(dllPath);
            var extracted = new List<Dictionary<string, string>>();
            
            var alphaRegex = new Regex("[a-zA-Z]");

            foreach (var type in module.Types)
            {
                foreach (var method in type.Methods)
                {
                    if (!method.HasBody) continue;

                    foreach (var instruction in method.Body.Instructions)
                    {
                        if (instruction.OpCode == OpCodes.Ldstr)
                        {
                            string str = instruction.Operand as string;
                            if (str != null && str.Length > 1 && alphaRegex.IsMatch(str))
                            {
                                // Basic filtering for Unity/internal strings
                                if (str.StartsWith("Assets/") || str.StartsWith("System.") || 
                                    str.StartsWith("UnityEngine.") || str.StartsWith("UI/"))
                                    continue;

                                var entry = new Dictionary<string, string>
                                {
                                    { "type", type.FullName },
                                    { "method", method.Name },
                                    { "offset", instruction.Offset.ToString("X4") },
                                    { "original", str },
                                    { "ru", "" }
                                };
                                extracted.Add(entry);
                            }
                        }
                    }
                }
            }

            var options = new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
            string json = JsonSerializer.Serialize(extracted, options);
            File.WriteAllText(outPath, json);

            Console.WriteLine($"Extracted {extracted.Count} string literals from Assembly-CSharp.dll");
        }
    }
}
