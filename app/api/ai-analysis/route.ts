import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { analysisResult, extractedText } = await request.json();

    if (!analysisResult) {
      return NextResponse.json(
        { error: 'Analysis result is required' },
        { status: 400 }
      );
    }

    // Extract detailed data for analysis
    const contactScore = Math.round((analysisResult.contactVerification?.score?.composite || analysisResult.contactVerification?.score?.overall_score || 0) * 100);
    const backgroundScore = Math.round((analysisResult.backgroundVerification?.score?.composite || 0) * 100);
    const digitalScore = analysisResult.digitalFootprint?.consistency_score || 0;
    const docScore = analysisResult.documentAuthenticity?.authenticityScore || 0;
    const aiConfidence = Math.round(analysisResult.aiDetection?.confidence || 0);

    // Create a data-driven AI analysis
    const mockAnalysis = `## Executive Summary
This candidate presents a **${getRiskLevel(contactScore, backgroundScore, digitalScore, docScore, aiConfidence)}** profile based on comprehensive verification analysis.

## Verification Analysis

### Contact Information (${contactScore}%)
${getContactAnalysis(contactScore, analysisResult)}

### Background Verification (${backgroundScore}%)
${getBackgroundAnalysis(backgroundScore, analysisResult)}

### Digital Footprint (${digitalScore}%)
${getDigitalAnalysis(digitalScore, analysisResult)}

### Document Authenticity (${docScore}%)
${getDocumentAnalysis(docScore, analysisResult)}

### AI Content Detection (${aiConfidence}% confidence)
${getAIAnalysis(aiConfidence, analysisResult)}

## Risk Assessment
${getRiskAssessment(contactScore, backgroundScore, digitalScore, docScore, aiConfidence)}

## Recommendations
${getRecommendations(contactScore, backgroundScore, digitalScore, docScore, aiConfidence, analysisResult)}`;

    // Helper functions for data-driven analysis
    function getRiskLevel(contact, background, digital, doc, ai) {
      const avgScore = (contact + background + digital + doc + (100 - ai)) / 5;
      if (avgScore >= 80) return "LOW RISK";
      if (avgScore >= 60) return "MODERATE RISK";
      return "HIGH RISK";
    }

    function getContactAnalysis(score, data) {
      if (score >= 80) return "✅ Strong verification with valid email and proper formatting";
      if (score >= 60) return "⚠️ Moderate verification - email valid but missing phone verification";
      return "❌ Weak verification - requires additional contact validation";
    }

    function getBackgroundAnalysis(score, data) {
      if (score >= 80) return "✅ Excellent background verification with strong company and education validation";
      if (score >= 60) {
        // Check if major companies are verified
        const companyEvidence = data.backgroundVerification?.company_evidence || {};
        const companies = Object.keys(companyEvidence);
        const majorCompanies = companies.filter(company => 
          company.toLowerCase().includes('amazon') || 
          company.toLowerCase().includes('microsoft') || 
          company.toLowerCase().includes('google') ||
          company.toLowerCase().includes('apple') ||
          company.toLowerCase().includes('meta') ||
          company.toLowerCase().includes('netflix') ||
          company.toLowerCase().includes('tesla')
        );
        
        if (majorCompanies.length > 0) {
          return `✅ Good background verification - major companies (${majorCompanies.join(', ')}) verified. Smaller companies may not be in public registries (normal for startups/small businesses)`;
        } else {
          return "⚠️ Moderate background verification - some companies verified but limited registry matches";
        }
      }
      return "❌ Weak background verification - limited registry matches require further investigation";
    }

    function getDigitalAnalysis(score, data) {
      if (score >= 80) return "✅ Strong digital presence with consistent professional footprint";
      if (score >= 60) return "⚠️ Moderate digital presence - some professional activity detected";
      return "❌ Limited digital presence - sparse online footprint may indicate gaps";
    }

    function getDocumentAnalysis(score, data) {
      if (score >= 80) return "✅ High document authenticity with standard formatting and metadata";
      if (score >= 60) return "⚠️ Moderate authenticity - some suspicious indicators but generally acceptable";
      return "❌ Low authenticity - multiple suspicious indicators suggest potential issues";
    }

    function getAIAnalysis(confidence, data) {
      if (confidence <= 20) return "✅ Low AI generation likelihood - appears to be human-written content";
      if (confidence <= 50) return "⚠️ Moderate AI generation likelihood - mixed signals detected";
      return "❌ High AI generation likelihood - content appears to be AI-generated";
    }

    function getRiskAssessment(contact, background, digital, doc, ai) {
      const issues = [];
      const positives = [];

      if (contact < 60) issues.push("Contact verification concerns");
      else positives.push("Strong contact verification");

      if (background < 60) issues.push("Background verification gaps");
      else positives.push("Good background verification");

      if (digital < 60) issues.push("Limited digital presence");
      else positives.push("Strong digital footprint");

      if (doc < 60) issues.push("Document authenticity concerns");
      else positives.push("Good document authenticity");

      if (ai > 50) issues.push("Potential AI generation");
      else positives.push("Human-written content");

      let assessment = "";
      if (positives.length > issues.length) {
        assessment = `**Overall Assessment**: This candidate shows more positive indicators than concerns. ${positives.join(", ")}.`;
      } else if (issues.length > positives.length) {
        assessment = `**Overall Assessment**: This candidate presents several areas of concern. ${issues.join(", ")}.`;
      } else {
        assessment = `**Overall Assessment**: Mixed verification results with both positive indicators and areas of concern.`;
      }

      return assessment;
    }

    function getRecommendations(contact, background, digital, doc, ai, data) {
      const recommendations = [];

      if (contact < 60) {
        recommendations.push("Request additional contact verification and phone number");
      }

      if (background < 70) {
        // Check if it's due to small companies vs actual issues
        const hasMajorCompany = data.backgroundVerification?.company_evidence && 
          Object.keys(data.backgroundVerification.company_evidence).some(company => 
            company.toLowerCase().includes('amazon') || 
            company.toLowerCase().includes('microsoft') || 
            company.toLowerCase().includes('google') ||
            company.toLowerCase().includes('apple')
          );
        
        if (hasMajorCompany) {
          recommendations.push("Major company verified - smaller companies may not be in public registries (normal for startups/small businesses)");
        } else {
          recommendations.push("Conduct thorough reference checks for all employers");
        }
      }

      if (digital < 60) {
        recommendations.push("Consider additional professional presence verification");
      }

      if (doc < 60) {
        recommendations.push("Request original document or additional authenticity verification");
      }

      if (ai > 50) {
        recommendations.push("Consider technical skills assessment to verify claimed expertise");
      }

      if (recommendations.length === 0) {
        recommendations.push("Proceed with standard hiring process - verification results are satisfactory");
      }

      return recommendations.map(rec => `- ${rec}`).join('\n');
    }

    return NextResponse.json({ analysis: mockAnalysis });

  } catch (error) {
    console.error('AI analysis error:', error);
    return NextResponse.json(
      { error: 'Failed to generate AI analysis' },
      { status: 500 }
    );
  }
}