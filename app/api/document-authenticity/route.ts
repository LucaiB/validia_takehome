import { NextRequest, NextResponse } from "next/server";
import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";

type DocumentMetadata = {
  fileName: string;
  fileSize: number;
  fileType: string;
  creationDate: string | null;
  modificationDate: string | null;
  author: string | null;
  creator: string | null;
  producer: string | null;
  title: string | null;
  subject: string | null;
  keywords: string | null;
  pdfVersion: string | null;
  pageCount: number | null;
  isEncrypted: boolean;
  hasDigitalSignature: boolean;
  softwareUsed: string | null;
  suspiciousIndicators: string[];
  authenticityScore: number; // 0-100, higher = more authentic
  rationale: string;
};

async function analyzeDocumentAuthenticity(client: BedrockRuntimeClient, metadata: DocumentMetadata): Promise<DocumentMetadata> {
  const prompt = `Analyze the following document metadata for authenticity and fraud indicators. Return ONLY a JSON object with the exact structure shown below.

Document Metadata:
- File Name: ${metadata.fileName}
- File Size: ${metadata.fileSize} bytes
- File Type: ${metadata.fileType}
- Creation Date: ${metadata.creationDate || 'Unknown'}
- Modification Date: ${metadata.modificationDate || 'Unknown'}
- Author: ${metadata.author || 'Unknown'}
- Creator: ${metadata.creator || 'Unknown'}
- Producer: ${metadata.producer || 'Unknown'}
- Title: ${metadata.title || 'Unknown'}
- Subject: ${metadata.subject || 'Unknown'}
- Keywords: ${metadata.keywords || 'Unknown'}
- PDF Version: ${metadata.pdfVersion || 'Unknown'}
- Page Count: ${metadata.pageCount || 'Unknown'}
- Is Encrypted: ${metadata.isEncrypted}
- Has Digital Signature: ${metadata.hasDigitalSignature}
- Software Used: ${metadata.softwareUsed || 'Unknown'}

Analyze for these fraud indicators:
1. Suspicious software names (e.g., "AI Resume Generator", "Fake Document Creator")
2. Unrealistic creation/modification times (same second, future dates)
3. Missing or suspicious author information
4. Unusual file properties (extremely small/large sizes)
5. Version inconsistencies
6. Generic or suspicious titles/subjects
7. Missing standard metadata fields
8. Signs of automated generation

Return JSON in this exact format:
{
  "suspiciousIndicators": ["indicator1", "indicator2"],
  "authenticityScore": 85,
  "rationale": "Brief explanation of the analysis"
}

Where authenticityScore is 0-100 (0 = highly suspicious, 100 = very authentic).`;

  const command = new InvokeModelCommand({
    modelId: "us.anthropic.claude-sonnet-4-20250514-v1:0",
    body: JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 800,
      temperature: 0,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    }),
    contentType: "application/json",
  });

  const response = await client.send(command);
  const responseBody = JSON.parse(new TextDecoder().decode(response.body));
  const content = responseBody.content?.[0]?.text ?? "{}";

  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]) as { suspiciousIndicators?: string[]; authenticityScore?: number; rationale?: string };
      return {
        ...metadata,
        suspiciousIndicators: parsed.suspiciousIndicators || [],
        authenticityScore: Math.max(0, Math.min(100, parsed.authenticityScore || 50)),
        rationale: parsed.rationale || "Unable to analyze metadata",
      };
    }
  } catch (error) {
    console.error("Failed to parse authenticity analysis:", error);
  }

  // Fallback if parsing fails
  return {
    ...metadata,
    suspiciousIndicators: ["Analysis failed"],
    authenticityScore: 50,
    rationale: "Unable to analyze document metadata",
  };
}

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File;
    
    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Set up AWS Bedrock client
    const region = process.env.AWS_REGION || "us-east-1";
    const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
    const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;

    if (!accessKeyId || !secretAccessKey) {
      return NextResponse.json({ error: "Server misconfigured: AWS credentials missing" }, { status: 500 });
    }

    const client = new BedrockRuntimeClient({
      region,
      credentials: {
        accessKeyId,
        secretAccessKey,
      },
    });

    const buffer = Buffer.from(await file.arrayBuffer());
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    let metadata: DocumentMetadata = {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      creationDate: null,
      modificationDate: null,
      author: null,
      creator: null,
      producer: null,
      title: null,
      subject: null,
      keywords: null,
      pdfVersion: null,
      pageCount: null,
      isEncrypted: false,
      hasDigitalSignature: false,
      softwareUsed: null,
      suspiciousIndicators: [],
      authenticityScore: 50,
      rationale: "",
    };

    // Extract metadata based on file type
    if (fileExtension === ".pdf") {
      try {
        console.log("Extracting PDF metadata...");
        const pdfLib = eval('require')('pdf-lib');
        const pdfDoc = await pdfLib.PDFDocument.load(buffer);
        
        const title = pdfDoc.getTitle();
        const author = pdfDoc.getAuthor();
        const subject = pdfDoc.getSubject();
        const keywords = pdfDoc.getKeywords();
        const creator = pdfDoc.getCreator();
        const producer = pdfDoc.getProducer();
        const creationDate = pdfDoc.getCreationDate();
        const modificationDate = pdfDoc.getModificationDate();
        
        metadata = {
          ...metadata,
          title: title || null,
          author: author || null,
          subject: subject || null,
          keywords: keywords || null,
          creator: creator || null,
          producer: producer || null,
          creationDate: creationDate ? creationDate.toISOString() : null,
          modificationDate: modificationDate ? modificationDate.toISOString() : null,
          pdfVersion: pdfDoc.getPDFVersion(),
          pageCount: pdfDoc.getPageCount(),
          isEncrypted: pdfDoc.isEncrypted,
          hasDigitalSignature: false, // pdf-lib doesn't directly support signature detection
          softwareUsed: producer || creator || null,
        };
        
        console.log("PDF metadata extracted successfully");
      } catch (error) {
        console.error("Failed to extract PDF metadata:", error);
        metadata.suspiciousIndicators.push("Failed to extract PDF metadata");
      }
    } else if (fileExtension === ".docx") {
      try {
        console.log("Extracting DOCX metadata...");
        const mammoth = eval('require')('mammoth');
        const docxData = await mammoth.extractRawText({ buffer });
        
        // For DOCX, we have limited metadata access with mammoth
        // In a real implementation, you'd use a library like 'officegen' or 'docx'
        metadata = {
          ...metadata,
          softwareUsed: "Microsoft Word", // Assumed for DOCX files
          pageCount: null, // Would need additional parsing
        };
        
        console.log("DOCX metadata extracted successfully");
      } catch (error) {
        console.error("Failed to extract DOCX metadata:", error);
        metadata.suspiciousIndicators.push("Failed to extract DOCX metadata");
      }
    }

    // Analyze the metadata for authenticity
    console.log("Analyzing document authenticity...");
    const analysisResult = await analyzeDocumentAuthenticity(client, metadata);
    console.log("Document authenticity analysis completed");

    return NextResponse.json(analysisResult, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
