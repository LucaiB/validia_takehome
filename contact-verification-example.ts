/**
 * Next.js Contact Verification Integration Example
 * 
 * This file demonstrates how to integrate the contact verification service
 * with your Next.js frontend application.
 */

// Types for the contact verification API
interface ContactVerifyRequest {
  full_name?: string;
  email: string;
  phone?: string;
  stated_location?: string;
  default_region?: string;
}

interface ContactVerifyResponse {
  email: {
    input: string;
    normalized: string;
    syntax_valid: boolean;
    domain_registrable: string;
    mx_records_found: boolean;
    smtp_probe: string;
    is_disposable: boolean;
    is_role: boolean;
    notes: string[];
    sources: string[];
  };
  phone?: {
    input: string;
    e164: string;
    valid: boolean;
    country_code: string;
    region_hint: string;
    toll_free: boolean;
    carrier?: string;
    timezone: string[];
    notes: string[];
    sources: string[];
  };
  geo_consistency?: {
    stated_location: string;
    phone_country_matches: boolean;
    phone_region_matches: boolean;
    toll_free_conflict: boolean;
    phone_region: string;
    phone_country: string;
    is_toll_free: boolean;
    method: string;
    sources: string[];
  };
  score: {
    email_score: number;
    phone_score: number;
    geo_score: number;
    composite: number;
  };
  rationale: string[];
}

/**
 * Call the contact verification API
 */
export async function callContactVerify(payload: ContactVerifyRequest): Promise<ContactVerifyResponse> {
  const res = await fetch(process.env.NEXT_PUBLIC_CONTACT_VERIFIER_URL + "/contact/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Contact verification failed: ${res.status} - ${errorText}`);
  }
  
  return res.json();
}

/**
 * React hook for contact verification
 */
import { useState, useCallback } from 'react';

export function useContactVerification() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ContactVerifyResponse | null>(null);

  const verifyContact = useCallback(async (payload: ContactVerifyRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await callContactVerify(payload);
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    verifyContact,
    isLoading,
    error,
    result,
  };
}

/**
 * Example React component using contact verification
 */
import React, { useState } from 'react';
import { useContactVerification } from './contact-verification-example';

export function ContactVerificationForm() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    stated_location: '',
  });

  const { verifyContact, isLoading, error, result } = useContactVerification();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await verifyContact({
        ...formData,
        default_region: 'US',
      });
    } catch (err) {
      // Error is handled by the hook
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Contact Verification</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Email *</label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Phone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Stated Location</label>
          <input
            type="text"
            value={formData.stated_location}
            onChange={(e) => setFormData({ ...formData, stated_location: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isLoading ? 'Verifying...' : 'Verify Contact'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Verification Results</h3>
          
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Composite Score:</span> {result.score.composite}
            </div>
            <div>
              <span className="font-medium">Email Score:</span> {result.score.email_score}
            </div>
            <div>
              <span className="font-medium">Phone Score:</span> {result.score.phone_score}
            </div>
            <div>
              <span className="font-medium">Geo Score:</span> {result.score.geo_score}
            </div>
          </div>

          <div className="mt-4">
            <h4 className="font-medium text-gray-900">Email Details:</h4>
            <ul className="text-sm text-gray-600 mt-1">
              <li>Syntax Valid: {result.email.syntax_valid ? 'Yes' : 'No'}</li>
              <li>MX Records: {result.email.mx_records_found ? 'Found' : 'Not Found'}</li>
              <li>Disposable: {result.email.is_disposable ? 'Yes' : 'No'}</li>
              <li>Role-based: {result.email.is_role ? 'Yes' : 'No'}</li>
            </ul>
          </div>

          {result.phone && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900">Phone Details:</h4>
              <ul className="text-sm text-gray-600 mt-1">
                <li>Valid: {result.phone.valid ? 'Yes' : 'No'}</li>
                <li>Country: {result.phone.country_code}</li>
                <li>Region: {result.phone.region_hint}</li>
                <li>Toll-free: {result.phone.toll_free ? 'Yes' : 'No'}</li>
                {result.phone.carrier && <li>Carrier: {result.phone.carrier}</li>}
              </ul>
            </div>
          )}

          {result.geo_consistency && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900">Geo Consistency:</h4>
              <ul className="text-sm text-gray-600 mt-1">
                <li>Country Matches: {result.geo_consistency.phone_country_matches ? 'Yes' : 'No'}</li>
                <li>Region Matches: {result.geo_consistency.phone_region_matches ? 'Yes' : 'No'}</li>
                <li>Toll-free Conflict: {result.geo_consistency.toll_free_conflict ? 'Yes' : 'No'}</li>
              </ul>
            </div>
          )}

          <div className="mt-4">
            <h4 className="font-medium text-gray-900">Rationale:</h4>
            <ul className="text-sm text-gray-600 mt-1 list-disc list-inside">
              {result.rationale.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Environment variable setup for Next.js
 * Add to your .env.local file:
 * 
 * NEXT_PUBLIC_CONTACT_VERIFIER_URL=http://localhost:8000
 */
